import sys
sys.path.append('../')
from dataset.LetorDataset import LetorDataset
from ranker.PDGDLinearRanker import PDGDLinearRanker
from clickModel.SDBN import SDBN
from clickModel.PBM import PBM
from utils import evl_tool
import numpy as np
import multiprocessing as mp
import pickle
import copy
import os
import random


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


def get_groups_dataset(train_set, intent_paths):
    num_groups = len(intent_paths)
    qrel_dics = []

    print("Reading intents......")
    for path in intent_paths:
        qrel_dics.append(read_intent_qrel(path))

    print("Randomly assign groups......")
    for qid in qrel_dics[0].keys():
        qid_rel_lists = []
        for qrel_dic in qrel_dics:
            doc_rels = {}
            for docid in qrel_dic[qid].keys():
                doc_rels[docid] = qrel_dic[qid][docid]
            qid_rel_lists.append(doc_rels)

        random.shuffle(qid_rel_lists)
        for i in range(len(qrel_dics)):
            for docid in qrel_dics[i][qid].keys():
                qrel_dics[i][qid][docid] = qid_rel_lists[i][docid]

    datasets = []
    print("Generating new datasets......")
    for qrel_dic in qrel_dics:
        new_train_set = copy.deepcopy(train_set)
        new_train_set.update_relevance_label(qrel_dic)
        datasets.append(new_train_set)
    return datasets

def run(train_set, ranker, num_interation, click_model):

    ndcg_scores = []
    cndcg_scores = []

    query_set = train_set.get_all_querys()
    index = np.random.randint(query_set.shape[0], size=num_interation)

    num_iter = 0
    current_train_set = train_set
    for i in index:

        qid = query_set[i]
        result_list, scores = ranker.get_query_result_list(current_train_set, qid)

        clicked_doc, click_label, _ = click_model.simulate(qid, result_list, current_train_set)

        ranker.update_to_clicks(click_label, result_list, scores, current_train_set.get_all_features_by_query(qid))

        if num_iter % 1000 == 0:
            all_result = ranker.get_all_query_result_list(current_train_set)
            ndcg = evl_tool.average_ndcg_at_k(current_train_set, all_result, 10)
            ndcg_scores.append(ndcg)

        cndcg = evl_tool.query_ndcg_at_k(current_train_set, result_list, qid, 10)
        cndcg_scores.append(cndcg)
        # print(num_iter, ndcg)
        num_iter += 1

    return ndcg_scores, cndcg_scores


def job(model_type, Learning_rate, NUM_INTERACTION, f, train_set, intent_paths, output_fold):
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

    for r in range(1, 26):
        random.seed(r)
        np.random.seed(r)
        datasets = get_groups_dataset(train_set, intent_paths)
        # create directory if not exist

        for i in range(len(datasets)):
            ranker = PDGDLinearRanker(FEATURE_SIZE, Learning_rate)

            print("PDGD intent fixed {} intent {} run{} start!".format(model_type, i, r))
            ndcg_scores, cndcg_scores = run(datasets[i], ranker, NUM_INTERACTION, cm)

            os.makedirs(os.path.dirname("{}/group{}/fold{}/".format(output_fold, i+1, f)), exist_ok=True)
            with open(
                    "{}/group{}/fold{}/{}_run{}_ndcg.txt".format(output_fold, i+1, f, model_type, r),
                    "wb") as fp:
                pickle.dump(ndcg_scores, fp)
            with open(
                    "{}/group{}/fold{}/{}_run{}_cndcg.txt".format(output_fold, i+1, f, model_type, r),
                    "wb") as fp:
                pickle.dump(cndcg_scores, fp)

            print("PDGD intent fixed {} intent {} run{} finished!".format(model_type, i, r))
            print()


if __name__ == "__main__":
    FEATURE_SIZE = 105
    NUM_INTERACTION = 200000
    click_models = ["informational", "navigational", "perfect"]
    # click_models = ["informational"]
    Learning_rate = 0.1

    dataset_path = "datasets/clueweb09_intent_change.txt"
    intent_path = "intents"
    output_fold = "results/SDBN/PDGD/group_fixed_200k"

    train_set = LetorDataset(dataset_path, FEATURE_SIZE, query_level_norm=True, binary_label=True)

    intent_paths = ["{}/1.txt".format(intent_path),
                    "{}/2.txt".format(intent_path),
                    "{}/3.txt".format(intent_path),
                    "{}/4.txt".format(intent_path)]

    for click_model in click_models:
        mp.Process(target=job, args=(click_model,
                                     Learning_rate,
                                     NUM_INTERACTION,
                                     1,
                                     train_set,
                                     intent_paths,
                                     output_fold)).start()