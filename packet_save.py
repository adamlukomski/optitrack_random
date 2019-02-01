import pickle

f = open('store.pckl', 'wb')
pickle.dump(packet, f)
f.close()