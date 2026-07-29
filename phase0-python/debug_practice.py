"""进阶篇 7/7《Jupyter与调试》· 动手任务 2

任务：实现一个故意有 bug 的函数
      （如对 [3, 1, 4, 1, 5] 求最大值但初始值写成 0，且列表可能全为负数），
      用 VS Code 断点单步定位 bug，修复后在注释里记录定位过程。

要求：注释里写清——断点打在哪、单步时观察到什么、bug 本质是什么。

另：任务 1 的 experiment.ipynb 和任务 3 的 explore_utils.py 见笔记原文，
    notebook 在 VS Code 里新建（先 uv add --dev ipykernel）。
"""


def my_max(nums: list[int]) -> int:

    # max_num = 0 警示，这样赋值会踩坑
    # 调试定位过程：
    # 1. 断点打在下面 max_num=0 初始化语句，然后一步步往下走。
    # 2. 单步调试时发现：当 nums 全是负数时，每个 num 都不大于初始值 0，
    #    因此 if 条件始终为 False，max_num 一直保持为 0。
    # 3. bug 本质：错误地假设最大值至少为 0。列表全为负数时，0 并不在列表中，
    #    却被当成了最大值。修复方式是使用列表第一个元素作为初始最大值。
    max_num = nums[0]

    for num in nums[1:]:
        if num > max_num:
            max_num = num

    return max_num


def main():
    max_num = 0
    nums = [-1, -1, -2, -4]
    max_num = my_max(nums)
    print(f"列表{nums}的最大值是{max_num}")
    nums2 = []
    # print(f"列表{nums2}的最大值是{my_max(nums2)}") 会报错list index out of range（数组下标越界），因为不存在下标0的数据
    print(f"列表{nums2}的最大值是{max（nums2]}")


if __name__ == "__main__":
    main()
