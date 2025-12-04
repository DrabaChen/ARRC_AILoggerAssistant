# ARRC AI Logger Assistant

**作者：**BG5CVB

**协议：**MIT License

**发布：**2025年12月4日

---

## 1. 这是什么？

**业余无线电点名（Amateur Radio Roll Call）AI日志辅助**，一款简易的业余无线电点名AI辅助工具，使用Python开发。

本程序主要希望解决主控对地名汉字不熟悉、记录速度跟不上参点台的报告速度等痛点。

因为有AI的帮助，点名主控可以随意记录点名的各项信息，让AI来完成结构化操作！



## 2. 准备上手

### a) 您的电脑可以运行Python代码吗？

请确保您的电脑拥有运行Python代码的环境。如果没有配置，请先查询相关教程，完成相关的配置。

这里有一份简单的Hello World程序。如果您是第一次尝试Python，可以选择它运行。

```python
print("Hello World!")
```

预期结果应该是看到输出"Hello World"在屏幕上。



### b) 获取大模型的API key

调用人工智能大模型，需要您自行获取相应的API key以接入。

**这会产生一笔费用。**不过在日常场景下，这个费用非常微小，通常在1元以内。

您可以选择心仪的大模型，例如DeepSeek或者通义千问等。你可以在以下网站找到它们的API key获取入口：

DeepSeek开放平台：https://platform.deepseek.com/

阿里云通义：https://bailian.console.aliyun.com/

……或者其他。

在获取之后，请将其设置为电脑的环境变量。

请注意！代码中默认的模型为`deepseek-chat`，环境变量名为`DEEPSEEK_API_KEY`。如果有与实际情况不一致，请进行相应的修改。

对应的代码行如下：

```python
def get_client():
    return OpenAI(
        api_key = os.getenv("DEEPSEEK_API_KEY"),	# 环境变量名
        base_url = "https://api.deepseek.com/v1",	# 大模型基地址
    )
```

```python
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",	# 模型名称，一共有2处
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": usr_prompt},
            ],
            stream = False,
            temperature = 0.8,
            response_format = {"type": "json_object"}
        )
```



### c) 安装缺失的模块

您可以尝试运行Python代码。非常有可能遇到模块缺失的问题。这时，您会发现以下报错：

```python
ModuleNotFoundError: No module named '...'
```

此时，请通过`pip`命令获取缺失的模块。在命令行中，运行：

```bash
pip install 模块名称
```

直到不再出现`ModuleNotFoundError`为止。



### d) 设置您的城市

为了让AI更好地匹配地名，请在程序开头处设置您的城市。城市默认为杭州。

```python
CITY = "杭州"
```



## 3. 如何使用

**本程序大小写不敏感。**因此，下列的所有命令、输入的内容，您都可以忽略大小写。



### a) 查看帮助（`HELP`或`H`）

输入`HELP`或者`H`查看帮助信息。



### b) 设置主控（`OP 呼号`）

输入命令`OP 呼号`来设置主控。在开始点名前或者点名途中均可更改。

开始点名前**一定要先设置好主控。**您会看到`[OP NOT SET!][Nr. 1] > `的提示符。

设置完毕后，提示符将会变成`[主控呼号][Nr. 1] > `。此时就可以记录点名内容，或者输入其他命令了。



### c) 记录点名，查看记录（`SHOW`）

本程序根据**《浙江省业余无线电协会中继台网点名规则》**的规定，需要记录**呼号、设备、天馈、功率、QTH**信息。在实践中，往往需要额外记录**高度信息**。当然，**通联时间、主控、RST（默认59）**与**序号**也是必要的，这些程序会自动填充。

由于我们使用了人工智能技术，所以本程序不像常见的辅助记录工具需要清晰写入每个字；您完全可以使用拼音等方式，尽可能快速、清晰而全面地记录参点台的相关信息。例如，

```text
[BG5CVB][Nr. 1] > bg5aaa laoheshan uvk6 30l 3eleyagi 5w
```

回车，交付AI处理。AI的响应速度大致为5秒左右。之后，您可以使用`SHOW`命令查看当前已经记录的点名内容：

```text
Record #1 added: BG5AAA - 2025-12-04 14:58
[BG5CVB][Nr. 2] > show

Current Records:
NR  DATE       UTC      CALL     RST   QTH             RIG             ANT             PWR      ALT      RMKS                
------------------------------------------------------------------------------------------------------------------------
1   2025-12-04 14:58    BG5AAA   59    老和山             UV-K6           3单元八木           5W       30楼      NULL
```



### d) 编辑记录（`EDIT 呼号`）

如果您发现AI记录有误，或者单纯希望更正某些内容，您可以通过`EDIT 呼号`来编辑记录。

输入呼号之后，如果有多条记录，您需要根据提示选择需要修改的那条。之后，输入更正内容，同样地，您可以随便写，不需要任何规范。

```text
[BG5CVB][Nr. 2] > edit bg5aaa
原始记录: #1 - BG5AAA - 老和山
请输入更正内容: hangzhouzhiwuyuan
记录 #1 已更新: BG5AAA - 2025-12-04 15:04
[BG5CVB][Nr. 2] > show

Current Records:
NR  DATE       UTC      CALL     RST   QTH             RIG             ANT             PWR      ALT      RMKS                
------------------------------------------------------------------------------------------------------------------------
1   2025-12-04 14:58    BG5AAA   59    杭州植物园           UV-K6           3单元八木           5W       30楼      NULL
```



### e) 查看状态（`STATUS`）

输入`STATUS`，您可以查看当前主控、QSO数量和下一序号。



### f) 快速保存（`SAVE`或`S`）

输入`SAVE`或`S`，快速保存当前的记录为备份`.json`文件。



### g) 快速读档（`LOAD`或`L`）

输入`LOAD`或`L`，快速读取上一份备份存档。



### h) 导出（`FINAL`或`SF`）

将当前的记录导出为`.csv`文件，以便后续处理与发布。



### i) 清除所有记录（`CLEAR`）

输入`CLEAR`，清除当前的所有记录。**请谨慎使用这个命令，尤其是当前未备份或者未导出的情况下。**



### j) 退出（`QUIT`）

输入`QUIT`，退出当前程序。**请谨慎使用这个命令，尤其是当前未备份或者未导出的情况下。**



## 4. 备注与声明

本程序尚未经过实测，欢迎各位爱好者在点名时尝试使用！

当然，根据本项目的**MIT License**，欢迎改进这份程序，使之更加趁手、人性化。

作者仅提供一个工具程序，请妥当使用。本项目的初衷与目的均仅为服务业余无线电点名活动。任何由于不当操作造成的后果，作者均不承担责任。敬请各位使用者留意。

其他未尽事宜，敬请留意后续更新。感谢您的理解与支持！