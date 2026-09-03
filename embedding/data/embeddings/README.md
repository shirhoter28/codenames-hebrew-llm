# Pretrained Hebrew embeddings

Do not commit vector tables (`.bin`, `.vec`, `.gz`, zip). They are gitignored.

## Word2Vec

NLPL model 47: Hebrew CoNLL17, skip-gram, 100-d, no lemmatization.

- Hugging Face: https://huggingface.co/Word2vec/nlpl_47
- NLPL zip: http://vectors.nlpl.eu/repository/20/47.zip

Place as `data/model.bin` or `data/embeddings/model.bin`.

Load with `KeyedVectors.load_word2vec_format(..., binary=True)` (word2vec C
binary, not gensim `.save()`).

Cite: Fares, Kutuzov, Oepen & Velldal (2017), NLPL word-vector repository.

## fastText (word-level `.vec` only)

Use the **text** dump so lookup is exact word match, like Word2Vec.

Wikipedia Hebrew: https://dl.fbaipublicfiles.com/fasttext/vectors-wiki/wiki.he.vec  
Save as `data/embeddings/wiki.he.vec`.

Larger Common-Crawl file (later if needed):
https://dl.fbaipublicfiles.com/fasttext/vectors-crawl/cc.he.300.vec.gz

Do **not** use `cc.he.300.bin` / `wiki.he.bin` until a subword/OOV condition
is explicitly added. Those Facebook binaries invent vectors for missing words.

Cite: Bojanowski, Grave, Joulin & Mikolov (2017).

Concatenation is built at run time (`--concat` / `--concat-guesser`):
L2-normalize each word in both tables, then join `[word2vec | fasttext]`. It
is not a third file to download. `--concat` is concat as **codemaster only**;
`--concat-guesser` is the added concat-guesser condition.

```bash
PYTHONPATH=. python scripts/check_embedding_coverage.py --model data/model.bin
PYTHONPATH=. python scripts/check_embedding_coverage.py --model data/embeddings/wiki.he.vec
```

## GloVe

No standard pretrained Hebrew GloVe comparable to English GloVe-840B. Skip
until a documented dump exists.
