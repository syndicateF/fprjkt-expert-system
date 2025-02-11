from gensim.models import KeyedVectors
print('load')
model = KeyedVectors.load_word2vec_format("model/cc.id.300.vec.gz", binary=False)
print('mulai save')
model.save("model/cc.id.300.bin")
print('save selsai')