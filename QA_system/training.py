# coding: utf-8

import tensorflow as tf
import numpy as np
import models
import config
import random
import argparse
import helper


def train(warm_start):
    train_c, train_q, _, _, emb_mat, voc = helper.load_dataset()

    dev_q = train_q[:int(len(train_c) / 10)]
    train_q = train_q[int(len(train_c) / 10):]

    total_train_loss = 0
    total_val_loss = 0

    min_val_loss = float("inf")

    with tf.Session() as sess:

        rm = models.RnnModel(emb_mat)
        saver = tf.train.Saver()
        writer = tf.summary.FileWriter(config.LOG_PATH, sess.graph)

        if warm_start:
            ckpt = tf.train.get_checkpoint_state(config.CKP_PATH)
            if ckpt and ckpt.model_checkpoint_path:
                saver.restore(sess, ckpt.model_checkpoint_path)
            else:
                print("Cannot restore model, does not exist")
                return
        else:
            sess.run(tf.global_variables_initializer())

        global_step = 0

        for epoch in range(config.TRANING_EPOCH):

            batch_counter = 0
            np.random.shuffle(train_q)
            while batch_counter < len(train_q):

                batch_sample = train_q[
                    batch_counter: batch_counter + config.BATCH_SIZE]

                batch_q, batch_c, batch_s, batch_e = helper.generate_batch(
                    batch_sample, voc, train_c)

                _, _, loss, summaries = sess.run([rm.opm_1, rm.opm_2, rm.loss, rm.merged],
                                                 feed_dict={rm.context_input: batch_c,
                                                            rm.question_input: batch_q,
                                                            rm.label_start: batch_s,
                                                            rm.label_end: batch_e,
                                                            rm.dropout_keep_prob: 0.8
                                                            })
                total_train_loss += loss
                print(
                    '''
                    global step: {},
                    current training loss is {},  
                    total average training loss is {}
                    '''.format(global_step, loss, total_train_loss / global_step))

                # every 8 global steps, sampling a batch to evaluate loss from
                # devel set
                if not global_step % 16:
                    dev_index = random.randint(0, len(dev_q) - 1)
                    dev_batch_sample = dev_q[
                        dev_index: dev_index + config.BATCH_SIZE]

                    dev_batch_q, dev_batch_c, dev_batch_s, dev_batch_e = helper.generate_batch(
                        dev_batch_sample, voc, train_c)

                    loss = sess.run(rm.loss, feed_dict={rm.context_input: dev_batch_c,
                                                        rm.question_input: dev_batch_q,
                                                        rm.label_start: dev_batch_s,
                                                        rm.label_end: dev_batch_e,
                                                        rm.dropout_keep_prob: 1
                                                        })

                    summary = tf.Summary()
                    summary_value = summary.value.add()
                    summary_value.simple_value = loss
                    summary_value.tag = "validation_loss"
                    writer.add_summary(summary, global_step)
                    total_val_loss += loss
                    print(
                        '''
                        current validation loss is {},
                        total average loss is {}
                        '''.format(loss, total_val_loss / global_step))

                writer.add_summary(summaries, global_step)
                batch_counter += config.BATCH_SIZE
                global_step += 1

        if min_val_loss >= total_val_loss:
            min_val_loss = total_val_loss
            save_path = saver.save(sess, config.CKPT_PATH + "rnet_v_00")

            print(
                '''
                Model saved in path: {} at time step {};
                Current eval loss is {}.
                '''.format(save_path, global_step, min_val_loss))

            rm.export_model(sess, config.RESULT_PATH)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--start_mode',
                        type=bool,
                        default=False,
                        help='Is warm start from existing checkpoint?')
    parsed_args = parser.parse_args()
    train(parsed_args.start_mode)
