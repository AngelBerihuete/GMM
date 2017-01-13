# -*- coding: UTF-8 -*-

import math
import argparse
import numpy as np
import tensorflow as tf
import pickle as pkl
import matplotlib.pyplot as plt

np.random.seed(7)
sess = tf.Session()

def tf_log_beta_function(x):
	return tf.sub(tf.reduce_sum(tf.lgamma(tf.add(x, np.finfo(np.float64).eps))), \
				  tf.lgamma(tf.reduce_sum(tf.add(x, np.finfo(np.float64).eps))))

def tf_dirichlet_expectation(alpha):
	if len(alpha.get_shape()) == 1:
		return tf.sub(tf.digamma(tf.add(alpha, np.finfo(np.float64).eps)), \
					  tf.digamma(tf.reduce_sum(alpha)))
	return tf.sub(tf.digamma(alpha), \
				  tf.digamma(tf.reduce_sum(alpha, 1))[:, tf.newaxis])

with open('../../data/data_k2_100.pkl', 'r') as inputfile:
	data = pkl.load(inputfile)
	xn = data['xn']

# plt.scatter(xn[:,0],xn[:,1], c=(1.*data['zn'])/max(data['zn']))
# plt.show()

N, D = xn.shape
K = 2
alpha_aux = [1.0, 1.0]
alpha = tf.convert_to_tensor([alpha_aux], dtype=tf.float64)
m_o_aux = np.array([0.0, 0.0])
m_o = tf.convert_to_tensor([list(m_o_aux)], dtype=tf.float64)
beta_o_aux = 0.01
beta_o = tf.convert_to_tensor(beta_o_aux, dtype=tf.float64)
Delta_o_aux = np.array([[1.0, 0.0], [0.0, 1.0]])
Delta_o = tf.convert_to_tensor(Delta_o_aux , dtype=tf.float64)

# Initialize
phi_aux = np.random.dirichlet(alpha_aux, N)
lambda_pi_aux = alpha_aux + np.sum(phi_aux, axis=0)
lambda_mu_beta_aux = beta_o_aux + np.sum(phi_aux, axis=0)
lambda_mu_m_aux = np.tile(1./lambda_mu_beta_aux, (2, 1)).T * \
				(beta_o_aux * m_o_aux + np.dot(phi_aux.T, data['xn']))
phi = tf.Variable(phi_aux, dtype=tf.float64)
lambda_pi = tf.Variable(lambda_pi_aux, dtype=tf.float64)
lambda_mu_beta = tf.Variable(lambda_mu_beta_aux, dtype=tf.float64)
lambda_mu_m = tf.Variable(lambda_mu_m_aux, dtype=tf.float64)

# Reshapes
lambda_mu_beta_res = tf.reshape(lambda_mu_beta, [K, 1])
lambda_pi_res = tf.reshape(lambda_pi, [K, 1])

init = tf.global_variables_initializer()
sess.run(init)

# ELBO 
ELBO = tf_log_beta_function(lambda_pi)
ELBO = tf.sub(ELBO, tf_log_beta_function(alpha))
ELBO = tf.add(ELBO, tf.matmul(tf.sub(alpha, lambda_pi), tf_dirichlet_expectation(lambda_pi_res)))
ELBO = tf.add(ELBO, tf.mul(tf.cast(K/2., tf.float64), tf.log(tf.matrix_determinant(tf.mul(beta_o, Delta_o)))))
ELBO = tf.add(ELBO, K*(D/2.))

# for k in range(K):
a1 = tf.sub(lambda_mu_m[1,:], m_o)
a2 = tf.matmul(Delta_o, tf.transpose(tf.sub(lambda_mu_m[1,:], m_o)))
a3 = tf.mul(tf.div(beta_o, 2.), tf.matmul(a1, a2))
a4 = tf.div(tf.mul(tf.cast(D, tf.float64), beta_o), tf.mul(tf.cast(2., tf.float64), lambda_mu_beta_res[1]))
a5 = tf.mul(tf.cast(1/2., tf.float64), tf.log(tf.mul(tf.pow(lambda_mu_beta_res[1], 2), tf.matrix_determinant(Delta_o))))
a6 = tf.add(a3, tf.add(a4, a5))
ELBO = tf.sub(ELBO, a6)
print('ELBO: {}'.format(sess.run(ELBO)))

b1 = tf.transpose(phi[:,1])
b2 = tf.sub(tf.cast(0., tf.float64), tf.log(phi[:,1]))
b3 = tf.mul(tf.cast(1/2., tf.float64), tf.log(tf.div(tf.matrix_determinant(Delta_o), tf.mul(tf.cast(2., tf.float64), math.pi))))
b4 = tf.sub(xn, lambda_mu_m[1,:])
b5 = tf.matmul(Delta_o, tf.transpose(tf.sub(xn, lambda_mu_m[1,:])))
b6 = tf.mul(tf.cast(1/2., tf.float64), tf.pack([tf.matmul(b4, b5)[i,i] for i in range(N)]))
b7 = tf.div(tf.cast(D, tf.float64), tf.mul(tf.cast(2., tf.float64), lambda_mu_beta[1]))
b8 = tf.add(b2, tf.sub(b3, tf.sub(b6, b7)))
print('ELBO: {}'.format(sess.run(ELBO)))

b1 = tf.reshape(b1, [1,N])
b8 = tf.reshape(b8, [1,N])
print('b1: {}'.format(sess.run(b1)))
print('b8: {}'.format(sess.run(b8)))
prod = tf.matmul(b1, b8, transpose_b=True)
print('b1*b8: {}'.format(sess.run(prod)))
print('ELBO: {}'.format(sess.run(ELBO)))
ELBO = tf.add(ELBO, prod)


"""
for n in range(N):
	b1 = phi[n,k]
	b2 = tf_dirichlet_expectation(lambda_pi)[k]
	b3 = tf.log(phi[n,k])
	b4 = tf.mul(1/2., tf.log(tf.div(tf.matrix_determinant(Delta_o), 2.*math.pi)))
	b5 = tf.sub(xn[n,:], lambda_mu_m[k,:])
	b6 = tf.matmul(Delta_o, tf.transpose(tf.sub(xn[n,:], lambda_mu_m[k,:])))
	b7 = tf.mul(1/2., tf.matmul(b5, b6))
	b8 = tf.div(tf.cast(D, tf.float64), tf.mul(2., lambda_mu_beta[1]))
	ELBO = tf.add(ELBO, tf.mul(b1, tf.sub(b2, tf.add(b3, tf.sub(b4, tf.sub(b7, b8))))))
"""

elbo = sess.run(ELBO)
print('Final ELBO={}'.format(elbo))