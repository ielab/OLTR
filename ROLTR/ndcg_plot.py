import pickle
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import sem, t
from utils.evl_tool import ttest
import scipy.stats as st
COLORS = ['C0', 'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'k']

def bar_plot(path, folds, runs, click_model, num_interactions, color, plot_ind, linestyle, marker, num_step=1):
    print("click model:", click_model)
    result = np.zeros(int(num_interactions / num_step))
    for f in folds:
        for r in runs:
            with open("{}/fold{}/{}_run{}.txt".format(path, f, click_model, r),
                      "rb") as fp:
                data = pickle.load(fp)
                data = np.array(data[:int(num_interactions / num_step)])
                result = np.vstack((result, data))
    result = np.mean(result[1:].T, axis=0)
    n = result.shape[0]

    result_mean = np.mean(result)
    result_std_err = sem(result)

    result_up, result_down = st.t.interval(0.95, n - 1, loc=result_mean, scale=result_std_err)
    print(result_up,result_mean, result_down)
    plt.bar(plot_ind, result_mean, width=0.35, color=COLORS[color], edgecolor='black', yerr=result_up-result_mean, capsize=7, label='poacee')
    plt.ylabel('Variance', fontsize=16)

def plot(path, folds, runs, click_model, num_interactions, color, plot_ind, linestyle, marker, num_step=1000):
    print("click model:", click_model)
    plt.subplot(2, 1, plot_ind + 1)
    # if click_model == 'informational':
    #     plt.title('noisy', loc='left', position=(0.01, 0.9), fontsize=16)
    # else:
    #     plt.title(click_model, loc='left', position=(0.01, 0.9), fontsize=16)
    if plot_ind == 0:
        plt.title('mlsr10k', loc='left', position=(0.01, 0.86), fontsize=16)

    result = np.zeros(int(num_interactions / num_step))
    for f in folds:
        for r in runs:
            with open("{}/fold{}/{}_run{}_ndcg.txt".format(path, f, click_model, r),
                      "rb") as fp:
                data = pickle.load(fp)
                data = np.array(data[:int(num_interactions / num_step)])
                result = np.vstack((result, data))
    result_list = result[1:, -1]
    result = result[1:].T
    n = result.shape[1]

    result_mean = np.mean(result, axis=1)
    result_std_err = sem(result, axis=1)
    result_up, result_down = st.t.interval(0.95, n-1, loc=result_mean, scale=result_std_err)

    plt.plot(range(0, num_interactions, num_step), result_mean, color=COLORS[color], alpha=1,
             linestyle=linestyle, marker=marker, markevery=10, markersize=10)

    plt.fill_between(range(0, num_interactions, num_step), result_up, result_down, color=COLORS[color], alpha=0.2)


    if plot_ind % 1 == 0:
        plt.ylabel('NDCG', fontsize=16)
        plt.xticks([])
    # if plot_ind // 1 == 1:
    #     plt.xticks(np.arange(0, 100001, 20000))
    #     plt.xlabel('impressions')
    # if plot_ind % 2 == 0:
    #     plt.ylabel('NDCG', fontsize=16)
    # plt.xlabel('impressions')

    plt.ylim([0.2, 0.45])
    # plt.yticks(np.arange(0.2, 0.36, 0.05))
    # plt.ylim([0.1, 0.55])
    # plt.xlim([0, 10000])
    # plt.xticks(np.arange(0, 10001, 2000))
    plt.xlabel('impressions', fontsize=16)
    print("result path:", path, result_mean[-1])
    return result_list


if __name__ == "__main__":
    ############## plot different reward function ####
    # path1 = "results/mslr10k/MDP_with_SGD_optimizer/MDP_001_both"
    # path2 = "results/mslr10k/MDP_with_SGD_optimizer/MDP_001_both_naive"
    # path3 = "results/mslr10k/MDP_with_SGD_optimizer/MDP_001_positive"
    # path4 = "results/mslr10k/MDP_with_SGD_optimizer/MDP_001_positive_naive"
    # path5 = "results/mslr10k/MDP_with_SGD_optimizer/MDP_001_negative"
    # path6 = "results/mslr10k/MDP_with_SGD_optimizer/MDP_001_negative_naive"
    # legends = ["$R_{IPS^{+}} + R_{IPS^{-}}$",
    #            "$R_{NAIVE^{+}} + R_{NAIVE^{-}}$",
    #            "$R_{IPS^{+}}$",
    #            "$R_{NAIVE^{+}}$",
    #            "$R_{IPS^{-}}$",
    #            "$R_{NAIVE^{-}}$"]

    ############## plot different propensities ####
    # path1 = "results/mslr10k/MDP_with_SGD_optimizer/MDP_001_both_naive"
    # path2 = "results/mslr10k/MDP_with_SGD_optimizer/MDP_001_both_propensity0.5"
    # path3 = "results/mslr10k/MDP_with_SGD_optimizer/MDP_001_both"
    # path4 = "results/mslr10k/MDP_with_SGD_optimizer/MDP_001_both_propensity1.5"
    # path5 = "results/mslr10k/MDP_with_SGD_optimizer/MDP_001_both_propensity2.0"
    # legends = ["$\eta=0$ (naive)",
    #            "$\eta=0.5$",
    #            "$\eta=1.0$ (true)",
    #            "$\eta=1.5$",
    #            "$\eta=2.0$"]

    ############## plot different gamma ####
    # path1 = "results/mslr10k/MDP_with_SGD_optimizer/MDP_001_positive_naive"
    # path2 = "results/mslr10k/MDP_with_SGD_optimizer/MDP_001_positive_naive_gamma1"
    # legends = ["$\gamma=0$",
    #            "$\gamma=1$"]

    ############# plot different variance ####
    # path1 = "results/mslr10k/MDP_with_SGD_optimizer/MDP_001_positive_naive_gamma0_variance"
    # path2 = "results/mslr10k/MDP_with_SGD_optimizer/MDP_001_positive_naive_gamma1_variance"
    # legends = ["$\gamma=0$",
    #            "$\gamma=1$"]

    ############## plot different algorithms ####
    path1 = "results/mslr10k/MDP_with_SGD_optimizer/MDP_001_both"
    path2 = "results/mslr10k/long_term_200k/PDGD"
    path3 = "results/mslr10k/DBGD"
    path4 = "results/mslr10k/PMGD"

    # path1 = "results/yahoo/MDP_with_SGD_optimizer/MDP_0005_both"
    # path2 = "results/yahoo/PDGD"
    # path3 = "results/yahoo/DBGD"
    # path4 = "results/yahoo/PMGD"
    #
    # path1 = "results/istella/MDP_with_SGD_optimizer/MDP_001_both"
    # path2 = "results/istella/PDGD"
    # path3 = "results/istella/DBGD"
    # path4 = "results/istella/PMGD"
    # #
    # path1 = "results/mq2007/MDP_001_both"
    # path2 = "results/mq2007/MDP_001_both_pairwise"
    # path3 = "results/mq2007/PDGD"
    # path4 = "results/mq2007/COLTR_gamma1"
    # path5 = "results/mq2007/PMGD"

    legends = ["ROLTR",
               "PDGD",
               "DBGD",
               "PMGD"]

    folds = list(range(1, 6))
    runs = list(range(1, 16))
    click_models = ["informational", "perfect"]
    # click_models = ["informational"]


    num_interactions = [100000]

    # plot different rewards
    f = plt.figure(1, figsize=(12, 4))

    plot_index = 0
    for click_model in click_models:
        for num_interaction in num_interactions:
            ############## plot different reward function ####
            # plot(path1, folds, runs, click_model, num_interaction, 0, plot_index, '-', None)
            # plot(path2, folds, runs, click_model, num_interaction, 0, plot_index, '--', None)
            # plot(path3, folds, runs, click_model, num_interaction, 5, plot_index, '-', None)
            # plot(path4, folds, runs, click_model, num_interaction, 5, plot_index, '--', None)
            # plot(path5, folds, runs, click_model, num_interaction, 4, plot_index, '-', None)
            # plot(path6, folds, runs, click_model, num_interaction, 4, plot_index, '--', None)

            ############## plot different propensies ####
            # plot(path1, folds, runs, click_model, num_interaction, 0, plot_index, '--', None)
            # plot(path2, folds, runs, click_model, num_interaction, 0, plot_index, '--', '+')
            # plot(path3, folds, runs, click_model, num_interaction, 0, plot_index, '-', None)
            # plot(path4, folds, runs, click_model, num_interaction, 0, plot_index, '--', 'x')
            # plot(path5, folds, runs, click_model, num_interaction, 0, plot_index, '--', '1')

            ############## plot different algorithms ####
            l1 = plot(path1, folds, runs, click_model, num_interaction, 0, plot_index, '-', None)
            l2 = plot(path2, folds, runs, click_model, num_interaction, 2, plot_index, '-', None)
            plot(path3, folds, runs, click_model, num_interaction, 6, plot_index, '-', None)
            plot(path4, folds, runs, click_model, num_interaction, 1, plot_index, '-', None)
            # print(ttest(l1, l2))

            ############## plot different gamma ####
            # plot(path1, folds, runs, click_model, num_interaction, 0, plot_index, '--', None)
            # plot(path2, folds, runs, click_model, num_interaction, 3, plot_index, '--', None)

            ############## plot different variance ####
            # bar_plot(path1, folds, runs, click_model, num_interaction, 0, plot_index-0.35/2, '--', None)
            # bar_plot(path2, folds, runs, click_model, num_interaction, 3, plot_index+0.35/2, '--', None)

            if plot_index == 0:
                plt.legend(legends, loc='lower right', ncol=4, fontsize=16)
            plot_index += 1
            print()
    # plt.xticks(np.arange(2), ("noisy", "perfect"), fontsize=16)
    f.subplots_adjust(wspace=0.13, hspace=0.05)
    f.set_size_inches(12, 4)
    plt.savefig('gammas.png', bbox_inches='tight')

    plt.show()
