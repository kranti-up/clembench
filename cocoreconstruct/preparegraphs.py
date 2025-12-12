import matplotlib.pyplot as plt


def avgturns_numshapes():
    #turns_cnt = {"2": 1.82, "3": 3.29, "4": 4.48, "5": 6.03}
    turns_cnt = {"2": 2, "3": 3, "4": 4, "5": 5}

    #plot the data
    x = list(turns_cnt.keys())
    y = [turns_cnt[k] for k in x]
    plt.plot(x, y, marker='o')
    plt.xlabel("Number of elements in the object")
    plt.ylabel("Average number of turns to reconstruct")
    #plt.title("Average Turns vs Number of Shapes")
    plt.grid(True)
    plt.savefig("avg_turns_num_elements.png")
    #plt.show()
    plt.close()

def avgcq_numshapes():
    turns_cnt_raw = {"2": 0, "3": 7, "4": 27, "5": 31}
    total_count = {"2": 120, "3": 126, "4": 126, "5": 128}
    turns_cnt = {}
    for k in turns_cnt_raw:
        turns_cnt[k] = (turns_cnt_raw[k]/ total_count[k])* 100.0  #/ 42.0 * 100.0

    #plot the data
    x = list(turns_cnt.keys())
    y = [turns_cnt[k] for k in x]
    plt.plot(x, y, marker='o')
    plt.xlabel("Number of elements in the object")
    plt.ylabel("Number of episodes with clarifications")
    #plt.title("Number of Episodes with Clarifications")
    plt.grid(True)
    plt.savefig("avg_cfq_num_elements.png")
    #plt.show()    
    plt.close()

def avgfail_numshapes():
    turns_cnt_raw = {"2": 7, "3": 11, "4": 31, "5": 26}
    total_count = {"2": 120, "3": 126, "4": 126, "5": 128}
    turns_cnt = {}
    for k in turns_cnt_raw:
        turns_cnt[k] = (turns_cnt_raw[k]/ total_count[k])* 100.0  #/ 42.0 * 100.0

    #plot the data
    x = list(turns_cnt.keys())
    y = [turns_cnt[k] for k in x]
    plt.plot(x, y, marker='o')
    plt.xlabel("Number of elements in the object")
    plt.ylabel("Number of episodes with failures")
    #plt.title("Number of Failures")
    plt.grid(True)
    plt.savefig("num_failures_num_elements.png")
    #plt.show()    
    plt.close()

def avgcorr_numshapes():
    turns_cnt_raw = {"2": 7, "3": 6, "4": 17, "5": 15}
    total_count = {"2": 120, "3": 126, "4": 126, "5": 128}
    turns_cnt = {}
    for k in turns_cnt_raw:
        turns_cnt[k] = (turns_cnt_raw[k]/ total_count[k])* 100.0  #/ 42.0 * 100.0    

    #plot the data
    x = list(turns_cnt.keys())
    y = [turns_cnt[k] for k in x]
    plt.plot(x, y, marker='o')
    plt.xlabel("Number of elements in the object")
    plt.ylabel("Number of episodes with corrections")
    #plt.title("Number of Episodes with Corrections")
    plt.grid(True)
    plt.savefig("num_episodes_corrections_num_elements.png")
    #plt.show()       
    plt.close() 


#avgturns_numshapes()
#avgcq_numshapes()
#avgfail_numshapes()
avgcorr_numshapes()