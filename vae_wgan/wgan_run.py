# Dependency imports
from absl import flags
import tensorflow_probability as tfp
from tools.get_data import *
from tools.statistics import *
from tools.analysis import *
tfd = tfp.distributions
tfb = tfp.bijectors


# Flags

def del_all_flags(FLAGS):
    flags_dict = FLAGS._flags()
    keys_list = [keys for keys in flags_dict]
    for keys in keys_list:
       FLAGS.__delattr__(keys)

del_all_flags(tf.flags.FLAGS)

flags = tf.app.flags
FLAGS = tf.flags.FLAGS

flags.DEFINE_bool(
    'noise_to_input',default=False, help="whether to add noise to training data")

flags.DEFINE_integer(
    "max_steps", default=20001, help="Number of training steps to run.")
flags.DEFINE_integer(
    "z_dim", default=128, help="dimension of latent z")
flags.DEFINE_integer("base_depth", default=32, help="Base depth for layers.")
flags.DEFINE_string(
    "activation",
    default="leaky_relu",
    help="Activation function for all hidden layers.")
flags.DEFINE_integer(
    "batch_size",
    default=64,
    help="Batch size.")
flags.DEFINE_integer(
    "n_samples", default=16, help="Number of samples to use in encoding.")

flags.DEFINE_float(
    "learning_rate_ger",
    default=5e-5,
    help="learning rate of the generator")
flags.DEFINE_float(
    "learning_rate_dis",
    default=5e-5,
    help="learning rate of the discriminator")
flags.DEFINE_integer(
    "img_size",
    default=32,
    help="size of the input image")
flags.DEFINE_integer(
    "channel",
    default=1,
    help="channel = 3 if is_svhn is True else 1")
flags.DEFINE_integer(
    "ngf",
    default=32,
    help="hidden layer size if mlp is chosen, ignore if otherwise")
flags.DEFINE_integer(
    "ndf",
    default=32,
    help="hidden layer size if mlp is chosen, ignore if otherwise")
flags.DEFINE_integer(
    "Citers",
    default=5,
    help="update Citers times of critic in one iter(unless i < 25 or i % 500 == 0, i is iterstep)")
flags.DEFINE_float(
    "clamp_lower",
    default=-0.01,
    help="the lower bound of parameters in critic")
flags.DEFINE_float(
    "clamp_upper",
    default=0.01,
    help="the upper bound of parameters in critic")
flags.DEFINE_bool(
    "is_mlp",
    default=False,
    help="where to use mlp or dcgan structure")
flags.DEFINE_bool(
    "is_adam",
    default=False,
    help="whether to use adam for parameter update, if the flag is set False"
         " use tf.train.RMSPropOptimizer as recommended in paper")
flags.DEFINE_bool(
    "is_svhn",
    default=False,
    help="whether to use SVHN or MNIST, set false and MNIST is used")
flags.DEFINE_string(
    "mode",
    default='gp',
    help="'gp' for gp WGAN and 'regular' for vanilla")
flags.DEFINE_float(
    "lam",
    default=10.,
    help="only when the mode is gp")
flags.DEFINE_string(
    "data_dir",
    default=os.path.join(os.getenv("TEST_TMPDIR", "/tmp"), "vae/data"),
    help="Directory where data is stored (if using real data).")
flags.DEFINE_string(
    "model_dir",
    default=os.path.join(os.getenv("TEST_TMPDIR", "/tmp"), "vae/"),
    help="Directory to put the model's fit.")
flags.DEFINE_integer(
    "viz_steps", default=1000, help="Frequency at which to save visualizations.")

flags.DEFINE_bool(
    "delete_existing",
    default=False,
    help="If true, deletes existing `model_dir` directory.")




def main(argv):
    del argv
  
    M = 5  # number of models in ensemble
    for i in range(M):
        params = FLAGS.flag_values_dict()
        params["activation"] = getattr(tf.nn, params["activation"])
       
        from wgan.model import model_fn
        FLAGS.model_dir = "gs://hyunsun/w_gan/mnist/model%d" % i

        if FLAGS.delete_existing and tf.gfile.Exists(FLAGS.model_dir):
            tf.logging.warn("Deleting old log directory at {}".format(FLAGS.model_dir))
            tf.gfile.DeleteRecursively(FLAGS.model_dir)
        tf.gfile.MakeDirs(FLAGS.model_dir)

        train_input_fn, eval_input_fn = get_dataset('mnist', FLAGS.batch_size)

        estimator = tf.estimator.Estimator(
            model_fn,
            params=params,
            config=tf.estimator.RunConfig(
                model_dir=FLAGS.model_dir,
                save_checkpoints_steps=FLAGS.viz_steps,
            ),
        )

        for _ in range(FLAGS.max_steps // FLAGS.viz_steps):
            estimator.train(train_input_fn, steps=FLAGS.viz_steps)
            #eval_results = estimator.evaluate(eval_input_fn)
            #print("Evaluation_results:\n\t%s\n" % eval_results)

    
    # plot values of variables defined in keys and plot them for each dataset

    # keys are threshold variables
    keys = ['true_logit']
    compare_datasets = ['mnist', 'mnist', 'mnist', 'mnist', 'mnist', 'mnist', 'notMNIST', 'fashion_mnist',
                        'fashion_mnist', 'normal_noise', 'uniform_noise']
    # whether to noise each dataset or not
    noised_list = [False, True, True, True, True, True, False, False, True, False, False]
    # if the element in noised_list is true for a dataset then what kind of noise/transformations to apply?
    # if the above element is set False, any noise/transformation will not be processed.

    noise_type_list = ['normal', 'normal', 'uniform', 'brighten', 'hor_flip', 'ver_flip', 'normal', 'normal', 'normal',
                       'normal', 'normal']

    # whether to add adversarially perturbed noise
    # if perturbed normal noise: normal, if perturbed uniform noise: uniform , if nothing: None
    show_adv_examples = 'normal'

    #if there is a specific range to look at, add a tuple of (low, high, #of bins) for the value
    bins = {'true_logit':(-5,5,100)}

    # out of the 5 models, which model to use for analysis
    which_model = 0


    FLAGS.model_dir = "gs://hyunsun/w_gan/mnist/model"
    expand_last_dim = True
    analysis(compare_datasets,expand_last_dim, noised_list, noise_type_list, show_adv_examples, model_fn, FLAGS.model_dir, which_model,
             which_model, keys, bins)


    # which model to use to create adversarially perturbed noise for ensemble analysis
    adv_base = 0
    compare_critic_preds(compare_datasets, expand_last_dim, noised_list, noise_type_list, FLAGS.batch_size,
                 model_fn, FLAGS.model_dir, show_adv_examples, adv_base)

if __name__ == "__main__":
    tf.app.run()

