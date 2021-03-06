./._word2vec_cbow.py                                                                                000644  000765  000024  00000000324 13157567714 015033  0                                                                                                    ustar 00mohan                           staff                           000000  000000                                                                                                                                                                             Mac OS X            	   2   ?      ?                                      ATTR       ?   ?   <                  ?   <  com.apple.quarantine q/0083;59c88149;Safari;FEB5EFB7-481E-465E-A21F-38B54672E67D                                                                                                                                                                                                                                                                                                             word2vec_cbow.py                                                                                    000644  000765  000024  00000013010 13157567714 014455  0                                                                                                    ustar 00mohan                           staff                           000000  000000                                                                                                                                                                         from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import math
import random

import numpy as np
from six.moves import urllib
from six.moves import xrange  # pylint: disable=redefined-builtin
import tensorflow as tf

from imdb_sentiment_data import get_dataset
from word2vec_fns import generate_batch, get_mean_context_embeds

vocabulary_size = 50000

data, count, dictionary, reverse_dictionary = get_dataset(vocabulary_size)

#print('Most common words (+UNK)', count[:5])
#print('Sample data', data[:10], [reverse_dictionary[i] for i in data[:10]])

# sanity check the batches
check_skip_window = 2      # How many words to consider left and right.
batch, labels = generate_batch(data, batch_size=8, skip_window=check_skip_window)
for i in range(8):
    print(batch[i, :], [reverse_dictionary[batch[i, j]] for j in range(check_skip_window*2)],
          '->', labels[i, 0], reverse_dictionary[labels[i, 0]])

# Step 4: Build and train a skip-gram model.

batch_size = 128
embedding_size = 100  # Dimension of the embedding vector.
skip_window = 1       # How many words to consider left and right.

# We pick a random validation set to sample nearest neighbors. Here we limit the
# validation samples to the words that have a low numeric ID, which by
# construction are also the most frequent.
valid_size = 16     # Random set of words to evaluate similarity on.
valid_window = 100  # Only pick dev samples in the head of the distribution.
valid_examples = np.random.choice(valid_window, valid_size, replace=False)
num_sampled = 64    # Number of negative examples to sample.

graph = tf.Graph()

with graph.as_default():

    # Input data.
    train_inputs = tf.placeholder(tf.int32, shape=[batch_size, 2*skip_window])
    train_labels = tf.placeholder(tf.int32, shape=[batch_size, 1])
    valid_dataset = tf.constant(valid_examples, dtype=tf.int32)

    # Ops and variables pinned to the CPU because of missing GPU implementation
    with tf.device('/cpu:0'):
        # Look up embeddings for inputs.
        embeddings = tf.Variable(
            tf.random_uniform([vocabulary_size, embedding_size], -1.0, 1.0))

        # train_inputs is of shape (batch_size, 2*skip_window)
        mean_context_embeds =\
            get_mean_context_embeds(embeddings, train_inputs)

        # Construct the variables for the NCE loss
        nce_weights = tf.Variable(
            tf.truncated_normal([vocabulary_size, embedding_size],
                                stddev=1.0 / math.sqrt(embedding_size)))
        nce_biases = tf.Variable(tf.zeros([vocabulary_size]))

        # Compute the average NCE loss for the batch.
        # tf.nce_loss automatically draws a new sample of the negative labels each
        # time we evaluate the loss.
        loss = tf.reduce_mean(
            tf.nn.nce_loss(weights=nce_weights,
                           biases=nce_biases,
                           labels=train_labels,
                           inputs=mean_context_embeds,
                           num_sampled=num_sampled,
                           num_classes=vocabulary_size))

        # Construct the SGD optimizer using a learning rate of 1.0.
        optimizer = tf.train.GradientDescentOptimizer(1.0).minimize(loss)

        # Compute the cosine similarity between minibatch examples and all embeddings.
        norm = tf.sqrt(tf.reduce_sum(tf.square(embeddings), 1, keep_dims=True))
        normalized_embeddings = embeddings / norm
        valid_embeddings = tf.nn.embedding_lookup(
            normalized_embeddings, valid_dataset)
        similarity = tf.matmul(
            valid_embeddings, normalized_embeddings, transpose_b=True)

    # Add variable initializer.
    init = tf.global_variables_initializer()

# Step 5: Begin training.
num_steps = 100001

saver = tf.train.Saver({'embedding':embeddings}, max_to_keep=None)


with tf.Session(graph=graph) as session:
    # We must initialize all variables before we use them.
    init.run()
    print('Initialized')

    average_loss = 0
    for step in xrange(num_steps):
        batch_inputs, batch_labels = generate_batch(data, batch_size, skip_window)
        feed_dict = {train_inputs: batch_inputs, train_labels: batch_labels}

        # We perform one update step by evaluating the optimizer op (including it
        # in the list of returned values for session.run()
        _, loss_val = session.run([optimizer, loss], feed_dict=feed_dict)
        average_loss += loss_val

        if step % 2000 == 0:
            if step > 0:
                average_loss /= 2000
            # The average loss is an estimate of the loss over the last 2000 batches.
            print('Average loss at step ', step, ': ', average_loss)
            average_loss = 0

        # Note that this is expensive (~20% slowdown if computed every 500 steps)
        if step % 10000 == 0:
            sim = similarity.eval()
            for i in range(valid_size):
                valid_word = reverse_dictionary[valid_examples[i]]
                top_k = 8  # number of nearest neighbors
                nearest = (-sim[i, :]).argsort()[1:top_k + 1]
                log_str = 'Nearest to %s:' % valid_word
                for k in range(top_k):
                    close_word = reverse_dictionary[nearest[k]]
                    log_str = '%s %s,' % (log_str, close_word)
                print(log_str)
            np.save("CBOW_Embeddings", normalized_embeddings.eval())
            #saver.save(session, 'w2vEmbedding', global_step=step)

    final_embeddings = normalized_embeddings.eval()
    np.save("CBOW_Embeddings", final_embeddings)
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        ./._word2vec_fns.py                                                                                 000644  000765  000024  00000000324 13157567714 014667  0                                                                                                    ustar 00mohan                           staff                           000000  000000                                                                                                                                                                             Mac OS X            	   2   ?      ?                                      ATTR       ?   ?   <                  ?   <  com.apple.quarantine q/0083;59c88149;Safari;FEB5EFB7-481E-465E-A21F-38B54672E67D                                                                                                                                                                                                                                                                                                             word2vec_fns.py                                                                                     000644  000765  000024  00000005517 13157567714 014326  0                                                                                                    ustar 00mohan                           staff                           000000  000000                                                                                                                                                                         import tensorflow as tf
import numpy as np
import collections

data_index = 0

def generate_batch(data, batch_size, skip_window):
    """
    Generates a mini-batch of training data for the training CBOW
    embedding model.
    :param data (numpy.ndarray(dtype=int, shape=(corpus_size,)): holds the
        training corpus, with words encoded as an integer
    :param batch_size (int): size of the batch to generate
    :param skip_window (int): number of words to both left and right that form
        the context window for the target word.
    Batch is a vector of shape (batch_size, 2*skip_window), with each entry for the batch containing all the context words, with the corresponding label being the word in the middle of the context
    """
    global data_index
    assert batch_size % num_skips == 0
    assert num_skips <= 2 * skip_window
    batch = np.ndarray(shape=(batch_size), dtype=np.int32)
    labels = np.ndarray(shape=(batch_size, 1), dtype=np.int32)
    span = 2 * skip_window + 1  # [ skip_window target skip_window ]
    buffer = collections.deque(maxlen=span)
    if data_index + span > len(data):
        data_index = 0
    buffer.extend(data[data_index:data_index + span])
    data_index += span
    for i in range(batch_size // num_skips):
        target = skip_window  # target label at the center of the buffer
        targets_to_avoid = [skip_window]
        for j in range(num_skips):
            # randomly sample a word in the context window, avoiding the target
            # word, and words already added (both stored in targets_to_avoid)
            while target in targets_to_avoid:
                target = random.randint(0, span - 1)
            targets_to_avoid.append(target)
            batch[i * num_skips + j] = buffer[skip_window]
            labels[i * num_skips + j, 0] = buffer[target]
        if data_index == len(data):
            # reached the end of the data, start again
            buffer.extend(data[:span])
            data_index = span
        else:
            # slide the window forward one word (n.b. buffer = deque(maxlen=span))
            buffer.append(data[data_index])
            data_index += 1
    # Backtrack a little bit to avoid skipping words in the end of a batch
    data_index = (data_index - span) % len(data)
    return batch, labels

def get_mean_context_embeds(embeddings, train_inputs):
    """
    :param embeddings (tf.Variable(shape=(vocabulary_size, embedding_size))
    :param train_inputs (tf.placeholder(shape=(batch_size, 2*skip_window))
    returns:
        `mean_context_embeds`: the mean of the embeddings for all context words
        for each entry in the batch, should have shape (batch_size,
        embedding_size)
    """
    # cpu is recommended to avoid out of memory errors, if you don't
    # have a high capacity GPU
    with tf.device('/cpu:0'):
        pass
    return mean_context_embeds
                                                                                                                                                                                 ./._plot_embeddings.py                                                                              000644  000765  000024  00000000324 13157567714 015425  0                                                                                                    ustar 00mohan                           staff                           000000  000000                                                                                                                                                                             Mac OS X            	   2   ?      ?                                      ATTR       ?   ?   <                  ?   <  com.apple.quarantine q/0083;59c88149;Safari;FEB5EFB7-481E-465E-A21F-38B54672E67D                                                                                                                                                                                                                                                                                                             plot_embeddings.py                                                                                  000644  000765  000024  00000002705 13157567714 015060  0                                                                                                    ustar 00mohan                           staff                           000000  000000                                                                                                                                                                         import numpy as np
import matplotlib

# if you get the error: "TypeError: 'figure' is an unknown keyword argument"
# uncomment the line below:
# matplotlib.use('Qt4Agg')

try:
    # pylint: disable=g-import-not-at-top
    from sklearn.manifold import TSNE
    import matplotlib.pyplot as plt
except ImportError as e:
    print(e)
    print('Please install sklearn, matplotlib, and scipy to show embeddings.')
    exit()

def plot_with_labels(low_dim_embs, labels, filename='tsne_embeddings.png'):
    assert low_dim_embs.shape[0] >= len(labels), 'More labels than embeddings'

    plt.figure(figsize=(18, 18))  # in inches
    for i, label in enumerate(labels):
        x, y = low_dim_embs[i, :]
        plt.scatter(x, y)
        plt.annotate(label,
                     xy=(x, y),
                     xytext=(5, 2),
                     textcoords='offset points',
                     ha='right',
                     va='bottom')

    plt.savefig(filename)
    print("plots saved in {0}".format(filename))

if __name__ == "__main__":
    # Step 6: Visualize the embeddings.
    reverse_dictionary = np.load("Idx2Word.npy").item()
    embeddings = np.load("CBOW_Embeddings.npy")
    tsne = TSNE(perplexity=30, n_components=2, init='pca', n_iter=5000, method='exact')
    plot_only = 500
    low_dim_embs = tsne.fit_transform(embeddings[:plot_only, :])
    labels = [reverse_dictionary[i] for i in range(plot_only)]
    plot_with_labels(low_dim_embs, labels)
    plt.show();
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           