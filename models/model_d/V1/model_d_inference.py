"""Model D inference: multilabel failure-risk categories for a startup description."""
import json, re
from pathlib import Path
import numpy as np, pandas as pd, joblib


class LSAEncoder:
    # Offline fallback text encoder: TF-IDF -> truncated SVD (LSA) -> L2-normalised vectors.
    # Same .encode() signature as SentenceTransformer, so the rest of the code is encoder-agnostic.
    def __init__(self, tfidf, svd):
        self.tfidf, self.svd = tfidf, svd

    @classmethod
    def fit(cls, texts, dim=256, seed=42):
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.decomposition import TruncatedSVD
        tfidf = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True, max_features=60000, stop_words="english")
        X = tfidf.fit_transform(texts)
        k = max(2, min(dim, X.shape[1] - 1, X.shape[0] - 1))
        svd = TruncatedSVD(n_components=k, random_state=seed).fit(X)
        return cls(tfidf, svd)

    def encode(self, texts, batch_size=64, normalize_embeddings=True, show_progress_bar=False, convert_to_numpy=True):
        Z = self.svd.transform(self.tfidf.transform(list(texts)))
        n = np.linalg.norm(Z, axis=1, keepdims=True); n[n == 0] = 1.0
        return (Z / n).astype(np.float32)



class FailureCategoryClassifier:
    NOTE = ("Categories are PREDICTED risk themes learned from historical failure narratives (weak, rule-derived labels). "
            "They are not confirmed causes and not a prediction that the startup will fail.")

    def __init__(self, artifact_dir):
        d = Path(artifact_dir)
        self.art = joblib.load(d / "model_d_classifier.joblib")
        cfg = json.loads((d / "label_config.json").read_text())
        self.rules = {k: re.compile("|".join(f"(?:{p})" for p in v), re.I) for k, v in cfg["rules"].items()}
        if self.art.get("encoder_kind", "sentence_transformer") == "lsa":
            self.encoder = LSAEncoder(self.art["lsa"]["tfidf"], self.art["lsa"]["svd"])     # offline fallback encoder
        else:
            from sentence_transformers import SentenceTransformer
            enc = d / "sentence_encoder"
            self.encoder = SentenceTransformer(str(enc) if enc.exists() else self.art["embed_model"])
        self.cases = pd.read_csv(d / "cases.csv")
        self.case_emb = np.load(d / "case_embeddings.npy")

    def _embed(self, texts):
        return np.asarray(self.encoder.encode(list(texts), normalize_embeddings=True, show_progress_bar=False,
                                              convert_to_numpy=True), dtype=np.float32)

    def _probs(self, E):
        a = self.art
        P = np.full((len(E), len(a["classes"])), np.nan)
        for j, c in enumerate(a["classes"]):
            if c in a["models"]:
                s = a["models"][c].decision_function(E)
                P[:, j] = a["calibrators"][c].predict_proba(s[:, None])[:, 1]
        return P

    def predict(self, text, top_k_cases=3):
        text = re.sub(r"\s+", " ", str(text or "")).strip()
        warnings = []
        if len(text.split()) < 20:
            warnings.append("Input is very short (<20 words); category estimates are unreliable.")
        if not text:
            return dict(model="D", categories=[], warnings=warnings + ["Empty input."], note=self.NOTE, meaning=self.art.get("card", {}).get("meaning"))

        a = self.art
        E = self._embed([text]); p = self._probs(E)[0]
        sents = [s for s in re.split(r"(?<=[.!?])\s+|\n+", text) if len(s.split()) >= 4]
        if len(sents) > 1:
            Ps = self._probs(self._embed(sents))
        else:
            sents, Ps = [text], p[None, :]
        sims = self.case_emb @ E[0]
        card = a.get("card", {})
        ood_cfg = card.get("ood", {})
        max_sim = float(sims.max())
        ood_flag = bool(ood_cfg) and max_sim < ood_cfg["sim_threshold"]
        if ood_flag:
            warnings.append(f"The text is unlike the historical failure narratives the model learned from (nearest-case similarity {max_sim:.2f} "
                            f"is below the typical lower bound {ood_cfg['sim_threshold']:.2f}). Treat the categories as weak signals.")

        out = []
        for j, c in enumerate(a["classes"]):
            if c not in a["models"]:
                out.append(dict(category=c, label=a["category_names"][c], supported=False,
                                reason="Not modelled: too few training examples."))
                continue
            kw = sorted({m.group(0).lower() for m in self.rules[c].finditer(text)})
            mask = (self.cases[c] == 1).values
            idx = np.where(mask)[0]
            top = idx[np.argsort(-sims[idx])[:top_k_cases]]
            out.append(dict(
                category=c, label=a["category_names"][c], supported=True,
                probability=round(float(p[j]), 4), threshold=round(a["thresholds"][c], 3),
                predicted=bool(p[j] >= a["thresholds"][c]),
                label_quality=card.get("label_quality", {}).get(c, "unknown"),
                evidence_sentence=sents[int(np.argmax(Ps[:, j]))],
                keyword_matches=kw,
                similar_historical_failures=[dict(name=self.cases.name[i], industry=self.cases.industry[i],
                                                  failure_reason=self.cases.failure_reason[i],
                                                  similarity=round(float(sims[i]), 3)) for i in top]))
        out.sort(key=lambda r: -r.get("probability", -1))
        predicted = [r["category"] for r in out if r.get("predicted")]
        if not predicted:
            warnings.append("No category reached its decision threshold. This does not mean the startup has no risks, only that the text does not "
                            "resemble the failure patterns this model knows.")
        for c in predicted:
            if c in card.get("low_precision_categories", []):
                warnings.append(f"'{a['category_names'][c]}': the labelling rule behind this category had low audited precision; treat it as unreliable.")
        return dict(model="D", categories=out, predicted_categories=predicted, warnings=warnings, note=self.NOTE,
                    meaning=card.get("meaning"), validation_status=card.get("validation_status"),
                    test_metrics=dict(original_text=card.get("test_metrics_original"), keyword_masked_text=card.get("test_metrics_keyword_masked")),
                    ood=dict(nearest_case_similarity=round(max_sim, 3), threshold=ood_cfg.get("sim_threshold"), flagged=ood_flag),
                    encoder=a.get("encoder_kind"))
