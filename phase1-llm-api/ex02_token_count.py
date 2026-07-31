"""阶段 1 · 《Token与上下文窗口》· 动手任务 1

任务：用 tiktoken 建立 token 直觉。
1. 准备一段中文文本（约 200 字）和一段意思相同的英文文本（约 200 词），分别数 token
2. 验证"中文吃 token"这个结论：算出中文的 token/字符 比值与英文的 token/词 比值
3. 顺带试试这几类内容的 token 数，感受差异：
   - 一段代码片段（比如 10 行 Java 或 Python）
   - 几个 emoji
   - 几个生僻字（如「龘」「靐」「爨」）

要求/提示：
- tiktoken 已装好，编码器选一个即可（不同模型编码器结果会不同，注释里记下你用的是哪个）
- 完成标准：打印出一张对比表，并在注释里写下"同样一句话，中文比英文贵多少倍"的结论
"""

import tiktoken


def main():
    enc = tiktoken.get_encoding("o200k_base")
    text0 = "两千三百多年前的一个傍晚，秦国边境的一家客舍外，站着一个走投无路的逃亡者。他想进去住一晚。店家摇头：对不起，商君定下的法令，收留没有凭证的客人，店家要连坐治罪。逃亡者站在门外，半天说不出话。过了许久，他仰天长叹了一声。那声叹息被史书记了下来，意思是：我立的法，它的弊病，竟然到了今天这个地步，连我自己，都被它堵在了门外。因为这个站在门外的人，就是商君本人。他叫商鞅。后人从他这声叹息里，提炼出一个成语：作法自毙。要讲这扇进不去的门，得先讲另一根木头。二十多年前，商鞅刚到秦国。那时的秦国，穷、乱、弱，被中原各国当成蛮夷看待，谁都能踩一脚。年轻的秦孝公发狠要变法图强，把这个从魏国来的读书人请进了宫。头一回见面，商鞅讲上古帝道，孝公听得直打瞌睡；第二回讲王道，还是提不起兴趣；第三回，讲霸道，讲富国强兵，孝公听得身子不由自主往前凑，一连谈了几天，不知疲倦。方向定了：变法。新法起草好了，商鞅却压着不发布。有人问他等什么。他说了两个字：不信。老百姓被官府糊弄了几百年，朝令夕改，说话不算数。法令再好，百姓不信，就是一张废纸。变法的第一仗，不是变法，是把'信'这个字立起来。于是，秦国都城的南门外，立起了一根三丈长的木头。旁边贴着告示：谁把这根木头搬到北门，赏十金。看热闹的人围了一层又一层，没人动手。搬根木头就给十金？天底下哪有这种好事，官府又在耍人。你想想，搁在今天，街上贴张告示说搬根木头给一套房，你敢不敢动手？人心里的怀疑，古今一个样。商鞅把赏金加到五十金。人群里终于走出来一个人，抱着试试看的心态，扛起木头，从南门走到北门。五十金，当场兑现，一个子儿不少。"
    text1 = "On an evening over 2300 years ago, outside a guesthouse on the border of Qin, stood a desperate fugitive. He wants to stay in for one night. The shop owner shook his head and said, 'I'm sorry, according to the law set by Mr. Shang, taking in guests without credentials will result in the shop owner being punished for both offenses. The fugitive stood outside the door, speechless for a long time. After a long time, he let out a long sigh and looked up at the sky. The sigh was brought down by Secretary Shi, which meant: The drawbacks of the law I established have reached such a point today that even I myself have been blocked by it. Because the person standing outside the door is none other than Mr. Shang himself. His name is Shang Yang. Later generations extracted an idiom from his sigh: 'Do as you wish and die.'. To talk about this inaccessible door, we have to first talk about another piece of wood. More than twenty years ago, Shang Yang had just arrived in the state of Qin. At that time, the state of Qin was poor, chaotic, and weak, and was treated as a barbarian by various countries in the Central Plains, where anyone could step on it. The young Duke Xiaogong of Qin, determined to reform and strengthen himself, invited this scholar from the state of Wei into the palace. The first time we met, Shang Yang talked about the ancient emperor's teachings, and Xiaogong fell asleep while listening; The second time I talked about the Way of King, I still couldn't muster any interest; In the third chapter, talking about hegemony and wealth and strong military, Xiaogong couldn't help but lean forward and talked tirelessly for several days. The direction has been set: reform. The new law has been drafted, but Shang Yang is holding back on publishing it. Someone asked him what he was waiting for. He said two words: I don't believe it. The common people have been fooled by the government for hundreds of years, constantly changing orders and not keeping their promises. No matter how good the law is, if the people don't believe it, it's just a piece of paper. The first battle of reform is not reform, but the establishment of the word 'faith'. So, outside the south gate of the capital city of Qin, a three zhang long wooden pole was erected. There is a notice next to it: Whoever moves this piece of wood to the north gate will receive ten gold coins. The onlookers surrounded layer after layer without anyone taking action. Moving a piece of wood for ten gold? There is no such good thing in the world, and the government is playing tricks on people again. Think about it, today there is a notice posted on the street saying to move a piece of wood to a house. Do you dare to take action? The doubts in people's hearts are the same throughout history. Shang Yang increased the bounty to fifty gold. Finally, a person walked out of the crowd with a try and see attitude, picked up a piece of wood, and walked from the south gate to the north gate. Fifty gold coins, cashed out on the spot, not a small amount."
    text_list = []
    text_list.append(text0)
    text_list.append(text1)
    text2 = "你好啊"
    text3 = "how are you"
    text_list.append(text2)
    text_list.append(text3)
    text4 = "a==b?1:0"
    text_list.append(text4)
    text5 = "[旺柴][机智][皱眉]"
    text_list.append(text5)
    text6 = "龘靐爨"
    text_list.append(text6)
    for i, text in enumerate(text_list):
        tokens = enc.encode(text)
        print(f"text{i} -> {len(tokens)} tokens")


if __name__ == "__main__":
    main()
# 输出如下：
# text0 -> 635 tokens
# text1 -> 655 tokens
# text2 -> 2 tokens
# text3 -> 3 tokens
# text4 -> 7 tokens
# text5 -> 11 tokens
# text6 -> 6 tokens
# 结论：同意或者近意常用词句的时候，中文比英文省token，中文生僻字、emoji比较费token，
