# 阶段 1 · 《大语言模型工作原理速览》· 动手任务 1 & 3（记录文件）

> 这是一份**实验记录**，由学员自己填写。下面的小标题是骨架，内容自己写。

## 任务 1：base 模型 vs instruct 模型

用 Ollama 分别跑一次 base 模型和 instruct 模型（如 `qwen2.5:7b-base` vs `qwen2.5:7b-instruct`），
输入同一句「介绍一下Java」，观察**续写**与**回答**的区别。

完成标准：能说清楚 base 模型为什么"不听话"，instruct 模型多做了什么（对齐/SFT）。

### 我跑的命令

<!-- ollama run qwen2.5:0.5b-base "介绍一下Java" -->
<!-- ollama run qwen2.5:0.5b-instruct "介绍一下Java" -->

### base 模型输出

<!-- Assistant:
Java是一种面向对象的编程语言，它提供了许多强大的工具和库来简化开发。以下是一些介绍Java的主要特点：

1. **静态类型系统（Static Typing）**：Java通过静态类型的机制来确保代码中的变量、方法和类的类型被严格定义。
2. **简单且高效的编译器（Java 8引入了反射机制，但早期版本使用的是ClassLoader API）**：Java提供了强大的工具来创建应用
程序、加载依赖项并处理异常。
3. **多线程支持**：Java提供了一个标准的多线程编程模型，使得在同一个进程中可以同时运行多个线程和任务。

4. **面向对象特性**：Java采用面向对象的设计模式和技术，如单例模式（Singleton）、工厂方法模式、接口（Interface）等。

5. **虚拟机（VM）**：Java通过JDK自带的虚拟机进行内存管理，并且使用了GC（Garbage Collector）来管理和回收垃圾。
6. **编译器支持**：尽管早期版本使用的是ClassLoader API，但Java现在依赖于Java Virtual Machine (JVM)来进行运行时环境和
动态代理等高级功能。

7. **跨平台性**：Java可以在不同的操作系统上运行，并且有很多优秀的库和支持它们的开发团队。
8. **安全性**：由于采用了严格的编码规范、API文档和其他安全措施，Java的安全性和性能通常优于其他一些编程语言。

总的来说，Java是一个强大而灵活的选择，适合于大型软件项目和需要大量并发处理的应用程序。 -->

### instruct 模型输出

<!-- Hello! Here is an introduction to Java:

1. What is Java?

Java is a high-level, object-oriented programming language that was designed for building applications and
systems. It has been developed by the Open Group in 2005 as part of its Family of Object-Oriented Standards
(JOAOS).

Java is known for being lightweight, fast, and efficient due to its platform independence and platform agnosticism
features.

2. How does Java work?

The basic structure of a Java program includes a main method that runs from the start until it exits or throws an
exception.

3. What is Java's syntax?

The Java language has a unique syntax that consists of two parts: source code and the runtime environment. The
source code represents the actual programming logic, while the runtime environment handles the execution of the
program.

4. How does Java handle memory management?

Java uses automatic memory management, meaning that it automatically manages memory for you when you create an
object or array. This means that your data will be automatically deallocated by the JVM (Java Virtual Machine)
when you no longer need to use it.

5. What are some features of Java?

Some key features of Java include:

- Large-scale platform independence: Because Java is platform-independent, you can write code once and run it on
any computer or device that runs Java.
- Platform agnosticism: You don't have to worry about specific operating systems or languages when writing your
application.
- Dynamic typing: Java allows dynamic types by using variables of different data types. This means that variable
values may be changed in the same way they were written, which is useful for managing memory and code reuse.
- Large libraries: Java has a wide range of classes and APIs available to help you quickly develop and test your
applications.

6. How does Java interact with operating systems?

Java can run on any platform that supports a runtime environment, such as Windows, macOS, Linux, and others.
However, Java is typically used in combination with other languages like C/C++, Python, Perl, Ruby, Perl, PHP,
JavaScript, Scala, Kotlin, Go, Rust, etc., which also run under the same JVM.

7. What are some common uses of Java?

Java can be used for developing desktop applications, web applications, mobile apps, and games. It's widely
supported in the Android operating system, Web applications, and large-scale software development projects.

8. How does Java compare to other programming languages?

Java is considered one of the most popular languages in the world. According to various sources, as of 2021, more
than 450 million developers worldwide use Java for their coding projects.

9. What are some challenges and limitations of using Java?

One challenge with Java is that it may not be suitable for large-scale or high-performance applications due to its
limited resources compared to other languages like C++, Python, etc. Another challenge relates to the platform
independence feature, as it can make certain features less accessible on certain platforms.

10. Are there any alternative programming languages for Java?

Yes, alternatives include: Kotlin (an open-source language by JetBrains), Swift (a popular programming language
developed by Apple) and Dart (a JavaScript-like language). -->


### 我跑的命令2

<!--  ollama run qwen2.5:0.5b-base "Java是一门" -->
<!--  ollama run qwen2.5:0.5b-instruct "Java是一门" -->

### base 模型输出
<!--ITIVE
itive

itive
itive
itive
itive
itive  -->

### instruct 模型输出
<!-- Java是阿里巴巴集团开发的编程语言，它具有以下特点：

1. 代码可移植性：Java是一种跨平台的语言，可以在不同的操作系统和硬件设备上运行。

2. 兼容性强：Java支持C/C++、C#等许多其他编程语言的标准接口，使得开发者可以使用它们来构建大型软件项目。

3. 并行处理能力强：Java利用多线程技术，使得程序在多个CPU核心之间并行执行任务，显著提高了程序的运行效率。

4. 依赖性强：Java依赖于标准库和JVM（Java Virtual Machine）的支持，因此需要一定的配置和维护成本。但其性能稳定、可扩展
性好等特点使其成为许多大型企业首选的语言。

5. 社区支持强：Java社区非常庞大，拥有众多的开发者和技术爱好者，这使得开发人员可以方便地获取技术支持和支持。  -->

### 结论

<!-- 
在明确的问题上，例如：“介绍一下JAVA”，两者有差距但是不多，base和instruct都完成了回答，不过instruct的回答更加详细，但是不知道为什么回答会变成英文

在不那么明确的问题“JAVA是一门”，base输出直接出现了问题，输出了一堆的乱码，而instruct则是正常的回答了，当成了JAVA是什么来回答，但是回答错误，居然说JAVA是阿里巴巴开发的

 -->

## 任务 3：显存估算与验证

心算并验证：**`qwen3.5:27b`** 的 Q4 量化大约占多少显存？
先写下你的**估算过程**（参数量 × 每参数字节数 + KV cache），再用 `ollama ps` 验证你的估算——
差多少、为什么差（提示：`ollama ps` 显示的是"模型权重 + 已分配 KV cache"）。

本机基线：RTX 2080 Ti 魔改 22GB 显存。模型已拉好，跑一次让它进显存再看 `ollama ps`。

### 我的估算

<!--  -->

### ollama ps 实测

<!-- 填写 -->

### 估算偏差与原因

<!-- 填写 -->
