import os
import pickle
import tensorflow as tf
import vectorizer.network.word2vec as network
import vectorizer.sampling as sampling
from vectorizer.nodeMap import nodeMap
from vectorizer.parameters import \
    NUM_FEATURES, LEARN_RATE, BATCH_SIZE, EPOCHS, CHECKPOINT_EVERY
from tensorflow.contrib.tensorboard.plugins import projector

'''
samples:批处理数据
logdir:checkpoint
outfile:embedding
'''


def learn_vectors(samples, logdir, outfile, num_feats=NUM_FEATURES, epochs=EPOCHS):
    """Learn a vector representation of Python AST nodes."""

    # build the inputs and outputs of the network
    input_node, label_node, embed_node, loss_node = network.init_net(
        num_feats=num_feats,
        batch_size=BATCH_SIZE
    )

    # use gradient descent with momentum to minimize the training objective
    train_step = tf.train.GradientDescentOptimizer(LEARN_RATE). \
        minimize(loss_node)

    tf.summary.scalar('loss', loss_node)

    ### init the graph
    sess = tf.Session()

    with tf.name_scope('saver'):
        saver = tf.train.Saver()
        summaries = tf.summary.merge_all()

        writer = tf.summary.FileWriter(logdir, sess.graph)
        config = projector.ProjectorConfig()
        embedding = config.embeddings.add()
        embedding.tensor_name = embed_node.name
        projector.visualize_embeddings(writer, config)

    sess.run(tf.global_variables_initializer())

    checkfile = os.path.join(logdir, 'ast2vec.ckpt')

    embed_file = open(outfile, 'wb')

    step = 0
    for epoch in range(1, epochs + 1):
        sample_gen = sampling.batchSamples(samples, BATCH_SIZE)
        for batch in sample_gen:
            input_batch, label_batch = batch

            _, summary, embed, err = sess.run(
                [train_step, summaries, embed_node, loss_node],
                feed_dict={
                    input_node: input_batch,
                    label_node: label_batch
                }
            )

            print('Epoch: ', epoch, 'Loss: ', err)
            writer.add_summary(summary, step)
            if step % CHECKPOINT_EVERY == 0:
                # save state so we can resume later
                saver.save(sess, os.path.join(checkfile), step)
                print('Checkpoint saved.')
                # save embeddings
                pickle.dump((embed, nodeMap), embed_file)
            step += 1

    # save embeddings and the mapping
    pickle.dump((embed, nodeMap), embed_file)
    embed_file.close()
    saver.save(sess, os.path.join(checkfile), step)
