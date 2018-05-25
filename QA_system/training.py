# coding: utf-8

import tensorflow as tf
import numpy as np
import pickle
import models
import constants as const
import random

with open("/mnt/training_data.pickle", "rb") as input_file:
    # training data is list of dictionary
    training_data = pickle.load(input_file)

emb_mat = np.load("/mnt/word_embedding_matrix.npy")
cm = models.CnnModel(emb_mat)

with open("/mnt/vocabulary.pickle", "rb") as input_file:
    voc = pickle.load(input_file)


def find_max_length(lst):
    length = max((len(e) for e in lst))
    return length


def convert_word_to_embedding_index(word, voc):
    if word in voc:
        return voc[word]
    else:
        return random.randint(0, len(voc) - 1)


with tf.Session() as sess:
    saver = tf.train.Saver()
    writer = tf.summary.FileWriter('model/train', sess.graph)

    sess.run(tf.global_variables_initializer())

    global_step = 0
    np.random.shuffle(training_data)

    for epoch in range(20):
        batch_i = 0
        while batch_i < len(training_data):
            start = batch_i
            end = batch_i + const.BATCH_SIZE

            batch_data = training_data[start: end]
            q_list = []
            c_list = []
            s_list = []
            e_list = []
            for ins in batch_data:
                q_list.append(list(map(lambda x: convert_word_to_embedding_index(x, voc), ins['question'])))
                c_list.append(list(map(lambda x: convert_word_to_embedding_index(x, voc), ins['context'])))
                s_list.append(ins['start'])
                e_list.append(ins['end'])

            # padding to a matrix by '0'
            max_q = find_max_length(q_list)
            for i in q_list:
                i.extend([0] * (max_q - len(i)))
            batch_q = np.asarray(q_list)

            max_c = find_max_length(c_list)
            for i in c_list:
                i.extend([0] * (max_c - len(i)))
            batch_c = np.asarray(c_list)

            max_s = find_max_length(s_list)
            for i in s_list:
                i.extend([0] * (max_s - len(i)))
            batch_s = np.asarray(s_list)

            max_e = find_max_length(e_list)
            for i in e_list:
                i.extend([0] * (max_e - len(i)))
            batch_e = np.asarray(e_list)

            print(batch_q.shape, batch_e.shape, batch_c.shape, batch_s.shape)
            _, loss, summaries = sess.run([cm.opm, cm.loss, cm.merged], feed_dict={cm.context_input: batch_c,
                                                                                   cm.question_input: batch_q,
                                                                                   cm.label_start: batch_s,
                                                                                   cm.label_end: batch_e,
                                                                                   cm.dropout_keep_prob: 0.8
                                                                                   })

            writer.add_summary(summaries, global_step)

            print("Epoch:", epoch, "loss:", loss)
            batch_i += const.BATCH_SIZE
            global_step += 1

        save_path = saver.save(sess, "model/cnn")
        print("Model saved in path: %s" % save_path)
