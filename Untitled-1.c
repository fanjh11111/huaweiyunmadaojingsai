#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define TYPE_NUM 7
#define SPEC_NUM 3
#define POP_SIZE 200
#define GENERATION 3000
#define MAX_PATTERN 1000
#define INF 1000000000

typedef struct {
    int spec;                   // 使用哪种原料规格
    int cnt[TYPE_NUM];          // 每种需求线材切几根
    int waste;                  // 该方案单根废料
} Pattern;

typedef struct {
    int gene[MAX_PATTERN];      // 每种切割方案使用多少根
    int fitness;                // 适应度，越小越好
    int waste;                  // 废料
    int stockCount[SPEC_NUM];   // 每种规格用多少根
} Individual;

int specLen[SPEC_NUM] = {20, 40, 60};              // 2m, 4m, 6m
int needLen[TYPE_NUM] = {5, 8, 12, 15, 35, 54, 50};
int demand[TYPE_NUM] = {100, 60, 40, 40, 35, 20, 10};

Pattern patterns[MAX_PATTERN];
Individual pop[POP_SIZE], newPop[POP_SIZE];

int patternNum = 0;

int randInt(int l, int r) {
    return l + rand() % (r - l + 1);
}

void generatePatternsDFS(int specId, int idx, int used, int cnt[]) {
    if (idx == TYPE_NUM) {
        int hasPiece = 0;

        for (int i = 0; i < TYPE_NUM; i++) {
            if (cnt[i] > 0) {
                hasPiece = 1;
                break;
            }
        }

        if (!hasPiece) return;

        patterns[patternNum].spec = specId;

        for (int i = 0; i < TYPE_NUM; i++) {
            patterns[patternNum].cnt[i] = cnt[i];
        }

        patterns[patternNum].waste = specLen[specId] - used;
        patternNum++;

        return;
    }

    int maxCnt = (specLen[specId] - used) / needLen[idx];

    for (int k = 0; k <= maxCnt; k++) {
        cnt[idx] = k;
        generatePatternsDFS(specId, idx + 1, used + k * needLen[idx], cnt);
    }

    cnt[idx] = 0;
}

void generatePatterns() {
    int cnt[TYPE_NUM] = {0};

    for (int i = 0; i < SPEC_NUM; i++) {
        generatePatternsDFS(i, 0, 0, cnt);
    }
}

void evaluate(Individual *ind) {
    int produce[TYPE_NUM] = {0};
    int totalRaw = 0;
    int totalNeed = 0;
    int shortagePenalty = 0;
    int excessPenalty = 0;

    for (int i = 0; i < SPEC_NUM; i++) {
        ind->stockCount[i] = 0;
    }

    for (int i = 0; i < patternNum; i++) {
        int g = ind->gene[i];

        if (g <= 0) continue;

        ind->stockCount[patterns[i].spec] += g;
        totalRaw += specLen[patterns[i].spec] * g;

        for (int j = 0; j < TYPE_NUM; j++) {
            produce[j] += patterns[i].cnt[j] * g;
        }
    }

    for (int i = 0; i < TYPE_NUM; i++) {
        totalNeed += needLen[i] * demand[i];

        if (produce[i] < demand[i]) {
            shortagePenalty += (demand[i] - produce[i]) * 100000;
        } else if (produce[i] > demand[i]) {
            excessPenalty += (produce[i] - demand[i]) * needLen[i] * 1000;
        }
    }

    ind->waste = totalRaw - totalNeed;

    if (ind->waste < 0) {
        ind->waste = 0;
    }

    ind->fitness = ind->waste + shortagePenalty + excessPenalty;
}

void initIndividual(Individual *ind) {
    for (int i = 0; i < patternNum; i++) {
        ind->gene[i] = 0;
    }

    /*
        随机初始化。
        使用次数不宜太大，否则容易产生大量多余线材。
    */
    for (int i = 0; i < patternNum; i++) {
        if (rand() % 100 < 8) {
            ind->gene[i] = randInt(0, 5);
        }
    }

    evaluate(ind);
}

int selectParent() {
    int best = randInt(0, POP_SIZE - 1);

    for (int i = 0; i < 3; i++) {
        int x = randInt(0, POP_SIZE - 1);

        if (pop[x].fitness < pop[best].fitness) {
            best = x;
        }
    }

    return best;
}

void crossover(Individual *a, Individual *b, Individual *child) {
    for (int i = 0; i < patternNum; i++) {
        if (rand() % 2) {
            child->gene[i] = a->gene[i];
        } else {
            child->gene[i] = b->gene[i];
        }
    }
}

void mutate(Individual *ind) {
    for (int i = 0; i < patternNum; i++) {
        if (rand() % 1000 < 15) {
            int delta = randInt(-2, 2);
            ind->gene[i] += delta;

            if (ind->gene[i] < 0) {
                ind->gene[i] = 0;
            }
        }
    }
}

int cmpIndividual(const void *a, const void *b) {
    Individual *x = (Individual *)a;
    Individual *y = (Individual *)b;
    return x->fitness - y->fitness;
}

void printBest(Individual *best) {
    int produce[TYPE_NUM] = {0};
    int totalRaw = 0;
    int totalNeed = 0;

    for (int i = 0; i < TYPE_NUM; i++) {
        totalNeed += needLen[i] * demand[i];
    }

    for (int i = 0; i < patternNum; i++) {
        int g = best->gene[i];

        if (g <= 0) continue;

        totalRaw += specLen[patterns[i].spec] * g;

        for (int j = 0; j < TYPE_NUM; j++) {
            produce[j] += patterns[i].cnt[j] * g;
        }
    }

    printf("较优下料结果：\n");
    printf("2米线材：%d 根\n", best->stockCount[0]);
    printf("4米线材：%d 根\n", best->stockCount[1]);
    printf("6米线材：%d 根\n", best->stockCount[2]);

    printf("\n总原料长度：%.1f 米\n", totalRaw / 10.0);
    printf("需求总长度：%.1f 米\n", totalNeed / 10.0);
    printf("废料长度：%.1f 米\n", (totalRaw - totalNeed) / 10.0);

    printf("\n各长度完成情况：\n");
    for (int i = 0; i < TYPE_NUM; i++) {
        printf("%.1f米：需求 %d 根，得到 %d 根\n",
               needLen[i] / 10.0, demand[i], produce[i]);
    }

    printf("\n使用的切割方案：\n");

    for (int i = 0; i < patternNum; i++) {
        if (best->gene[i] > 0) {
            printf("原料 %.1f米，使用 %d 根：",
                   specLen[patterns[i].spec] / 10.0,
                   best->gene[i]);

            for (int j = 0; j < TYPE_NUM; j++) {
                if (patterns[i].cnt[j] > 0) {
                    printf(" %.1f米x%d",
                           needLen[j] / 10.0,
                           patterns[i].cnt[j]);
                }
            }

            printf("，单根废料 %.1f米\n", patterns[i].waste / 10.0);
        }
    }
}

int main() {
    srand((unsigned int)time(NULL));

    generatePatterns();

    for (int i = 0; i < POP_SIZE; i++) {
        initIndividual(&pop[i]);
    }

    for (int gen = 0; gen < GENERATION; gen++) {
        qsort(pop, POP_SIZE, sizeof(Individual), cmpIndividual);

        // 保留前 10 个优秀个体
        for (int i = 0; i < 10; i++) {
            newPop[i] = pop[i];
        }

        for (int i = 10; i < POP_SIZE; i++) {
            int p1 = selectParent();
            int p2 = selectParent();

            crossover(&pop[p1], &pop[p2], &newPop[i]);
            mutate(&newPop[i]);
            evaluate(&newPop[i]);
        }

        for (int i = 0; i < POP_SIZE; i++) {
            pop[i] = newPop[i];
        }
    }

    qsort(pop, POP_SIZE, sizeof(Individual), cmpIndividual);

    printBest(&pop[0]);

    return 0;
}