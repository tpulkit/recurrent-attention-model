#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File: mnist_center.py
# Author: Qian Ge <geqian1001@gmail.com>

import os
import sys
import numpy as np
import tensorflow as tf
import platform
import scipy.misc
import argparse
import matplotlib.pyplot as plt
import read_mnist as read

sys.path.append('../')
from lib.models.dram import DRAM
import lib.utils.viz as viz
from lib.helper.trainer import Trainer


if platform.node() == 'arostitan':
    # DATA_PATH = '/home/qge2/workspace/data/MNIST_data/'
    SAVE_PATH = '/home/qge2/workspace/data/out/dram/'
elif platform.node() == 'Qians-MacBook-Pro.local':
    pass
    # DATA_PATH = '/Users/gq/Google Drive/Foram/Training/simple_1/'
else:
    # DATA_PATH = 'E:/GITHUB/workspace/topologyseg/simple_gap/'
    SAVE_PATH = 'E:/GITHUB/workspace/dram/'

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--predict', action='store_true',
                        help='Run prediction')
    parser.add_argument('--train', action='store_true',
                        help='Train the model')
    parser.add_argument('--test', action='store_true',
                        help='Test')
    parser.add_argument('--trans', action='store_true',
                        help='Transform image')
    parser.add_argument('--center', action='store_true',
                        help='Center')

    parser.add_argument('--step', type=int, default=4,
                        help='Number of glimpse')
    parser.add_argument('--sample', type=int, default=1,
                        help='Number of location samples during training')
    parser.add_argument('--glimpse', type=int, default=8,
                        help='Glimpse base size')
    parser.add_argument('--batch', type=int, default=128,
                        help='Batch size')
    parser.add_argument('--epoch', type=int, default=1000,
                        help='Max number of epoch')
    parser.add_argument('--load', type=int, default=100,
                        help='Load pretrained parameters with id')
    parser.add_argument('--lr', type=float, default=1e-3,
                        help='Init learning rate')
    parser.add_argument('--std', type=float, default=0.03,
                        help='std of location')
    parser.add_argument('--pixel', type=int, default=26,
                        help='unit_pixel')
    parser.add_argument('--scale', type=int, default=2,
                        help='scale of glimpse')
    
    return parser.parse_args()

# class config_center():
#     step = 6
#     sample = 1
#     glimpse = 8
#     n_scales = 1
#     batch = 128
#     epoch = 1000
#     loc_std = 0.03
#     unit_pixel = 12

# class config_transform():
#     step = 6
#     sample = 1
#     glimpse = 12
#     n_scales = 3
#     batch = 128
#     epoch = 2000
#     loc_std = 0.03
#     unit_pixel = 26

if __name__ == '__main__':
    FLAGS = get_args()


    # test
    # n_hidden=[10, 10]
    # n_linear_hidden=10
    # b_size = 10
    # lr = 0.01

    # # train
    n_hidden=[512, 512]
    n_linear_hidden=256
    b_size = 128
    # lr = 0.01

    train_data = read.train_data
    valid_data = read.valid_data
    train_data.setup(epoch_val=0, batch_size=b_size)
    valid_data.setup(epoch_val=0, batch_size=b_size)

    model = DRAM(im_size=100,
                 n_channel=1,
                 n_hidden=n_hidden,
                 n_linear_hidden=n_linear_hidden,
                 n_step=FLAGS.step,
                 location_std=0.03,
                 glimpse_base_size=FLAGS.glimpse,
                 n_glimpse_scale=FLAGS.scale,
                 unit_pixel=20,
                 n_class=10,
                 coarse_size=32)
    model.create_model()
    # train_op = model.train_op()
    # REINFORCE_loss = model.REINFORCE_loss
    # cls_loss = model.cls_loss
    # accuracy_op = model.get_accuracy()
    # summary_op = model.get_summary()

    saver = tf.train.Saver()
    writer = tf.summary.FileWriter(SAVE_PATH)
    if FLAGS.train:
        trainer = Trainer(model, train_data, init_lr=FLAGS.lr)

        sessconfig = tf.ConfigProto()
        sessconfig.gpu_options.allow_growth = True
        with tf.Session(config=sessconfig) as sess:
            sess.run(tf.global_variables_initializer())
            for epoch_id in range(0, FLAGS.epoch):
                trainer.train_epoch(sess, summary_writer=writer)
                trainer.valid_epoch(sess, valid_data, batch_size=128)
                saver.save(sess, '{}dram-epoch-{}'.format(SAVE_PATH, epoch_id))
            # acc_sum = 0
            # for step in range(0, 10000):

            #     batch_data = train_data.next_batch_dict()
            #     _, loss_1, loss_2, acc, cur_summary, cur_lr, g, l = sess.run(
            #         [train_op, REINFORCE_loss, cls_loss, accuracy_op, summary_op, model.cur_lr, model.g,
            #         model.layers['l_sample']], 
            #         feed_dict={model.lr: FLAGS.lr,
            #                    model.image: batch_data['im'],
            #                    model.cls_label: batch_data['label']})
            #     # print(loss_1, loss_2)
            #     # print(l)
            #     acc_sum += acc
            #     if step % 100 == 0:
            #         test_acc_sum = 0
            #         for test_step in range(0, 10):
            #             acc = sess.run(
            #                 accuracy_op, 
            #                 feed_dict={
            #                            model.image: batch_data['im'],
            #                            model.cls_label: batch_data['label']})
            #             test_acc_sum += acc
            #         print('train: {:.02f}, valid: {:.02f}, lr: {:.05f}'.format(acc_sum / 100., test_acc_sum / 10., cur_lr))
            #         acc_sum = 0

            #         saver.save(sess, 
            #                    '{}dram-step-{}'.format(SAVE_PATH, FLAGS.step),
            #                    global_step=step)
            #         writer.add_summary(cur_summary, step)

    if FLAGS.test:
        valid_data.setup(epoch_val=0, batch_size=20)
        size = FLAGS.glimpse
        scale = FLAGS.scale
        unit_pixel = 20
        im_size = 100
        l_range = im_size / 2.0 / (1.0 * unit_pixel)

        model.set_is_training(False)
        saver = tf.train.Saver()
        sessconfig = tf.ConfigProto()
        sessconfig.gpu_options.allow_growth = True
        with tf.Session(config=sessconfig) as sess:
            sess.run(tf.global_variables_initializer())
            saver.restore(
                sess, '{}dram-epoch-{}'.format(SAVE_PATH, 50))

            batch_data = valid_data.next_batch_dict()
            # test_im = batch_data['im'].astype(float)
            loc_list, pred, input_im, glimpses = sess.run(
                [model.layers['l_sample'], model.layers['pred'],
                model.image, model.layers['retina_reprsent']],
                feed_dict={model.image: batch_data['im']})
                

            pad_r = size * (2 ** (scale - 2))
            im_size = input_im[0].shape[0]
            loc_list = np.clip(np.array(loc_list), -l_range, l_range) / l_range
            # print('loc_list')
            # print(loc_list)
                # print('test')
                # print(test)
            loc_list = loc_list * 1.0 * (im_size / 2) / (im_size / 2 + pad_r)
            loc_list = (loc_list + 1.0) * 1.0 / 2 * (im_size + pad_r * 2)
                # loc_list = (loc_list + l_range) * 1.0 * unit_pixel
            offset = pad_r

            print(pred)
            # print(loc_list)
            for step_id, cur_loc in enumerate(loc_list):
                im_id = 0
                glimpse = glimpses[step_id]
                for im, loc, cur_glimpse in zip(input_im, cur_loc, glimpse):
                    im_id += 1                
                    fig, ax = plt.subplots(1)
                    ax.imshow(np.squeeze(im), cmap='gray')
                    for scale_id in range(0, scale):
                        cur_size = size * 2 ** scale_id
                        side = cur_size * 1.0 / 2
                        x = loc[1] - side - offset
                        y = loc[0] - side - offset
                        viz.draw_bbx(ax, x, y, cur_size)
                        # plt.show()
                    for i in range(0, scale):
                        patch = np.squeeze(cur_glimpse[:,:,i])
                        # patch = np.squeeze(cur_glimpse[:,:,i] * 255)
                        # patch = patch.astype(np.uint8)
                            # patch = np.clip(patch, 0, 255)
                        scipy.misc.imsave(
                            os.path.join(SAVE_PATH,'im_{}_glimpse_{}_step_{}.png').format(im_id, i, step_id),
                            patch)
                            # print(cur_glimpse[:,:,i])
                    plt.savefig(os.path.join(
                        SAVE_PATH,'im_{}_step_{}.png').format(im_id, step_id))
                    plt.close(fig)

            # print(loss_1, loss_2)

    # FLAGS = get_args()
    # if FLAGS.trans:
    #     name = 'trans'
    #     config = config_transform()
    # elif FLAGS.center:
    #     name = 'centered'
    #     config = config_center()
    # else:
    #     FLAGS.trans = True
    #     name = 'custom'
    #     class config_FLAGS():
    #         step = FLAGS.step
    #         sample = FLAGS.sample
    #         glimpse = FLAGS.glimpse
    #         n_scales = FLAGS.scale
    #         batch = FLAGS.batch
    #         epoch = FLAGS.epoch
    #         loc_std = FLAGS.std
    #         unit_pixel = FLAGS.pixel
    #     config = config_FLAGS()

    # train_data = MNISTData('train', data_dir=DATA_PATH, shuffle=True)
    # train_data.setup(epoch_val=0, batch_size=config.batch)
    # valid_data = MNISTData('val', data_dir=DATA_PATH, shuffle=True)
    # valid_data.setup(epoch_val=0, batch_size=10)

    # model = RAMClassification(
    #                           im_channel=1,
    #                           glimpse_base_size=config.glimpse,
    #                           n_glimpse_scale=config.n_scales,
    #                           n_loc_sample=config.sample,
    #                           n_step=config.step,
    #                           n_class=10,
    #                           max_grad_norm=5.0,
    #                           unit_pixel=config.unit_pixel,
    #                           loc_std=config.loc_std,
    #                           is_transform=FLAGS.trans)
    # model.create_model()

    # trainer = Trainer(model, train_data, init_lr=FLAGS.lr)
    # writer = tf.summary.FileWriter(SAVE_PATH)
    # saver = tf.train.Saver()

    # sessconfig = tf.ConfigProto()
    # sessconfig.gpu_options.allow_growth = True
    # with tf.Session(config=sessconfig) as sess:
    #     sess.run(tf.global_variables_initializer())
    #     if FLAGS.train:
    #         writer.add_graph(sess.graph)
    #         for step in range(0, config.epoch):
    #             trainer.train_epoch(sess, summary_writer=writer)
    #             trainer.valid_epoch(sess, valid_data, config.batch)
    #             saver.save(sess, 
    #                        '{}ram-{}-mnist-step-{}'
    #                        .format(SAVE_PATH, name, config.step),
    #                        global_step=step)
    #             writer.close()

    #     if FLAGS.predict:
    #         valid_data.setup(epoch_val=0, batch_size=20)
    #         saver.restore(sess, 
    #                       '{}ram-{}-mnist-step-6-{}'
    #                       .format(SAVE_PATH, name, FLAGS.load))
            
    #         batch_data = valid_data.next_batch_dict()
    #         trainer.test_batch(
    #             sess,
    #             batch_data,
    #             unit_pixel=config.unit_pixel,
    #             size=config.glimpse,
    #             scale=config.n_scales,
    #             save_path=RESULT_PATH)