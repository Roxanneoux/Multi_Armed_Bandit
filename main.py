import numpy as np
import matplotlib.pyplot as plt

class BernoulliBandit:
    #伯努利多臂老虎机,输入k表示拉杆个数
    def __init__(self, K):
        self.probs = np.random.uniform(size=K)      #随机生成K个0~1的数，作为拉动每根拉杆的奖励
        self.best_idx = np.argmax(self.probs)       #获奖概率最大的拉杆
        self.best_prob = self.probs[self.best_idx]  #最大的获奖概率
        self.K = K

    def step(self, k):
        #当玩家选择了k号拉杆后，根据拉动该老虎机的k号拉杆获得奖励的概率返回1（获奖）或0（未获奖）
        #对老虎机而言，执行某个动作后，是否获得奖励是不确定的
        ran = np.random.rand()
        if ran < self.probs[k]:
            return 1
        else:
            return 0

np.random.seed(1)           #设计随机种子，使实验具有可重复性
K = 10
bandit_10_arm = BernoulliBandit(K)
print("获得概率最大的拉杆为%d号,其获奖概率为%.4f"%
      (bandit_10_arm.best_idx, bandit_10_arm.best_prob))


class Solver:
    #多臂老虎机算法基本框架
    def __init__(self, bandit):
        self.bandit = bandit
        self.counts = np.zeros(self.bandit.K)        #每根拉杆的尝试次数
        self.regret = 0                             #当前步的累计懊悔
        self.actions = []                           #维护一个列表，记录每一步的动作
        self.regrets = []                           #维护一个列表，记录每一步的累计懊悔

    def update_regret(self, k):
        #计算累计懊悔并保存，k为每次动作选择的拉杆编号
        self.regret += self.bandit.best_prob - self.bandit.probs[k]
        self.regrets.append(self.regret)

    def run_one_step(self):
        #返回当前动作选择哪一根拉杆，由每个具体的策略实现
        #在父类中先预留一个方法接口不实现，在其子类中实现。如果要求其子类一定要实现，不实现的时候会导致问题，那么采用raise的方式就很好。而此时产生的问题分类是NotImplementedError。
        raise NotImplementedError

    def run(self, num_steps):
        #运行一定次数，num_steps为总运行次数
        for _ in range(num_steps):
            k = self.run_one_step()
            self.counts[k] += 1
            self.actions.append(k)
            self.update_regret(k)


class EpsilonGreedy(Solver):
    #epsilon贪婪算法，继承Solver类
    def __init__(self, bandit, epsilon=0.01, init_prob=1.0):
        super(EpsilonGreedy, self).__init__(bandit)
        self.epsilon = epsilon
        #初始化拉动所有拉杆的期望奖励估值
        self.estimates = np.array([init_prob] * self.bandit.K)

    def run_one_step(self):
        if np.random.random() < self.epsilon:
            k = np.random.randint(0, self.bandit.K)        #随机选择一根拉杆
        else:
            k = np.argmax(self.estimates)               #选择期望奖励估值最大的拉杆

        r = self.bandit.step(k)                         #得到本次动作的奖励
        self.estimates[k] += 1. / (self.counts[k] + 1) * (r - self.estimates[k])
        #self.counts的值在Solver类的run()函数部分变化

        return k

class DecayingEpsilonGreedy(Solver):
    """ epsilon值随时间衰减的epsilon-贪婪算法,继承Solver类 """
    def __init__(self, bandit, init_prob=1.0):
        super(DecayingEpsilonGreedy, self).__init__(bandit)
        self.estimates = np.array([init_prob] * self.bandit.K)
        self.total_count = 0

    def run_one_step(self):
        self.total_count += 1
        if np.random.random() < 0.01 - 1 / self.total_count:  # epsilon值随时间衰减
            k = np.random.randint(0, self.bandit.K)
        else:
            k = np.argmax(self.estimates)

        r = self.bandit.step(k)
        self.estimates[k] += 1. / (self.counts[k] + 1) * (r - self.estimates[k])

        return k

class UCB(Solver):
    #UCB算法，继承Solver类
    def __init__(self, bandit, coef, init_prob=1.0):
        super(UCB, self).__init__(bandit)
        self.total_count = 0
        self.estimates = np.array([init_prob] * self.bandit.K)
        self.coef = coef

    def run_one_step(self):
        self.total_count += 1
        ucb = self.estimates + self.coef * np.sqrt(np.log(self.total_count) / (2 * (self.counts + 1)))      #计算上置信界
        #由于每个拉杆的被拉次数不同，self.counts的值不同，因此每个动作增加的不确定性度量不同

        k = np.argmax(ucb)      #计算上置信界最大的拉杆
        #UCB算法与贪婪算法的区别在于：k（执行动作）的选择策略不同

        r = self.bandit.step(k)
        self.estimates[k] += 1. / (self.counts[k] + 1) * (r - self.estimates[k])
        return k


def plot_results(solvers, solver_names):
    for idx, solver in enumerate(solvers):
        time_list = range(len(solver.regrets))
        plt.plot(time_list, solver.regrets, label=solver_names[idx])
    plt.xlabel('Time steps')
    plt.ylabel('Cumulative regrets')
    plt.title('%d-armed bandit' % solvers[0].bandit.K)
    plt.legend()
    plt.show()
    plt.savefig('result')

np.random.seed(1)
epsilon_greedy_solver = EpsilonGreedy(bandit_10_arm)
coef = 1            #控制不确定性比重的系数
UCB_solver = UCB(bandit_10_arm, coef)
epsilon_greedy_solver.run(5000)
UCB_solver.run(5000)
decaying_epsilon_greedy_solver = DecayingEpsilonGreedy(bandit_10_arm)
decaying_epsilon_greedy_solver.run(5000)
print('epsilon-贪婪算法的累计懊悔为：', epsilon_greedy_solver.regret)
print('UCB算法的累计懊悔为：', UCB_solver.regret)
print('decaying-epsilon-贪婪算法的累计懊悔为：', decaying_epsilon_greedy_solver.regret)
solver_names = ['EpsilonGreedy', 'UCB', 'decaying_epsilon_greedy']
plot_results([epsilon_greedy_solver, UCB_solver, decaying_epsilon_greedy_solver], solver_names)

