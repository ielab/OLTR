import sys
sys.path.append('../')
from dataset.LetorDataset import LetorDataset
from ranker.COLTRLinearRanker import COLTRLinearRanker
from clickModel.SDBN import SDBN
from clickModel.PBM import PBM
from utils import evl_tool
import numpy as np
import multiprocessing as mp
import pickle
import copy
import os

def read_intent_qrel(path: str):

    # q-d pair dictionary
    qrel_dic = {}

    with open(path, 'r') as f:
        for line in f:
            qid, _, docid, rel = line.strip().split()
            if qid in qrel_dic.keys():
                qrel_dic[qid][docid] = int(rel)
            else:
                qrel_dic[qid] = {docid: int(rel)}
    return qrel_dic

def get_intent_dataset(train_set, test_set, intent_path):
    new_train_set = copy.deepcopy(train_set)
    new_test_set = copy.deepcopy(test_set)
    qrel_dic = read_intent_qrel(intent_path)
    new_train_set.update_relevance_label(qrel_dic)
    new_test_set.update_relevance_label(qrel_dic)
    return new_train_set, new_test_set


def run(train_intents, test_intents, ranker, num_interation, click_model, num_rankers):
    ndcg_scores = []
    cndcg_scores = []

    query_set = train_intents[0].get_all_querys()
    index = np.random.randint(query_set.shape[0], size=num_interation)
    num_iter = 0

    current_train_set = train_intents[0]
    current_test_set = test_intents[0]
    for i in index:
        if num_iter % 10000 == 0 and num_iter > 0:
            # print("Change intent to", int(num_iter/10000))
            all_result = ranker.get_all_query_result_list(current_test_set)
            ndcg = evl_tool.average_ndcg_at_k(current_test_set, all_result, 10)
            ndcg_scores.append(ndcg)

            current_train_set = train_intents[int(num_iter/10000)]
            current_test_set = test_intents[int(num_iter / 10000)]

        qid = query_set[i]
        result_list = ranker.get_query_result_list(current_train_set, qid)

        clicked_doc, click_label, _ = click_model.simulate(qid, result_list, current_train_set)

        # if no clicks, skip.
        if len(clicked_doc) == 0:
            if num_iter % 100 == 0:
                all_result = ranker.get_all_query_result_list(current_test_set)
                ndcg = evl_tool.average_ndcg_at_k(current_test_set, all_result, 10)
                ndcg_scores.append(ndcg)

            cndcg = evl_tool.query_ndcg_at_k(current_train_set, result_list, qid, 10)
            cndcg_scores.append(cndcg)
            # print(num_inter, ndcg, "continue")
            num_iter += 1
            continue

        # flip click label. exp: [1,0,1,0,0] -> [0,1,0,0,0]
        last_click = np.where(click_label == 1)[0][-1]
        click_label[:last_click + 1] = 1 - click_label[:last_click + 1]

        # bandit record
        record = (qid, result_list, click_label, ranker.get_current_weights())

        unit_vectors = ranker.sample_unit_vectors(num_rankers)
        canditate_rankers = ranker.sample_canditate_rankers(
            unit_vectors)  # canditate_rankers are ranker weights, not ranker class

        # winner_rankers are index of candidates rankers who win the evaluation
        winner_rankers = ranker.infer_winners(canditate_rankers[:num_rankers],
                                              record)

        if winner_rankers is not None:
            gradient = np.sum(unit_vectors[winner_rankers - 1], axis=0) / winner_rankers.shape[0]
            ranker.update(gradient)

        if num_iter % 100 == 0:
            all_result = ranker.get_all_query_result_list(current_test_set)
            ndcg = evl_tool.average_ndcg_at_k(current_test_set, all_result, 10)
            ndcg_scores.append(ndcg)

        cndcg = evl_tool.query_ndcg_at_k(current_train_set, result_list, qid, 10)
        cndcg_scores.append(cndcg)
        # print(num_inter, ndcg)
        num_iter += 1

    return ndcg_scores, cndcg_scores


def job(model_type, f, train_intents, test_intents, tau, step_size, gamma, num_rankers, learning_rate_decay, output_fold):
    if model_type == "perfect":
        pc = [0.0, 1.0]
        ps = [0.0, 0.0]

    elif model_type == "navigational":
        pc = [0.05, 0.95]
        ps = [0.2, 0.9]

    elif model_type == "informational":
        pc = [0.3, 0.7]
        ps = [0.1, 0.5]
    # cm = PBM(pc, 1)
    cm = SDBN(pc, ps)


    for r in range(1, 16):
        # np.random.seed(r)
        ranker = COLTRLinearRanker(FEATURE_SIZE, Learning_rate, step_size, tau, gamma, learning_rate_decay=learning_rate_decay)

        print("COLTR intent change {} fold{} run{} start!".format(model_type, f, r))
        ndcg_scores, cndcg_scores = run(train_intents, test_intents, ranker, NUM_INTERACTION, cm, num_rankers)

        # create directory if not exist
        os.makedirs(os.path.dirname("{}/fold{}/".format(output_fold, f)), exist_ok=True)
        with open(
                "{}/fold{}/{}_run{}_ndcg.txt".format(output_fold, f, model_type, r),
                "wb") as fp:
            pickle.dump(ndcg_scores, fp)
        with open(
                "{}/fold{}/{}_run{}_cndcg.txt".format(output_fold, f, model_type, r),
                "wb") as fp:
            pickle.dump(cndcg_scores, fp)
        print("COLTR intent change {} fold{} run{} finished!".format(model_type, f, r))
        print()


if __name__ == "__main__":

    FEATURE_SIZE = 105
    NUM_INTERACTION = 50000
    # click_models = ["informational", "navigational", "perfect"]
    click_models = ["informational", "perfect"]
    # click_models = ["perfect"]
    Learning_rate = 0.1

    dataset_fold = "datasets/intent_change_mine"
    output_fold = "results/SDBN/COLTR/intent_change"

    num_rankers = 499
    tau = 0.1
    gamma = 1
    learning_rate_decay = 1
    step_size = 1

    # for 5 folds
    for f in range(1, 6):
        training_path = "{}/Fold{}/train.txt".format(dataset_fold, f)
        test_path = "{}/Fold{}/test.txt".format(dataset_fold, f)

        train_set = LetorDataset(training_path, FEATURE_SIZE, query_level_norm=True, binary_label=True)
        test_set = LetorDataset(test_path, FEATURE_SIZE, query_level_norm=True, binary_label=True)

        train_set1, test_set1 = get_intent_dataset(train_set, test_set, "1.txt")
        train_set2, test_set2 = get_intent_dataset(train_set, test_set, "2.txt")
        train_set3, test_set3 = get_intent_dataset(train_set, test_set, "3.txt")
        train_set4, test_set4 = get_intent_dataset(train_set, test_set, "4.txt")

        train_intents = [train_set1, train_set2, train_set3, train_set4, train_set1]
        test_intents = [test_set1, test_set2, test_set3, test_set4, test_set1]

        # for 3 click_models
        for click_model in click_models:
            p = mp.Process(target=job, args=(click_model, f, train_intents, test_intents,
                                             tau, step_size, gamma, num_rankers, learning_rate_decay, output_fold))
            p.start()
