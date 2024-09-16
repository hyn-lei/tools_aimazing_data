import json
import logging
import traceback

import tiktoken
from langchain.callbacks import StreamingStdOutCallbackHandler
from openai import OpenAI

from config.config import settings
from test.test_rapid_api import langchain_translate, langchain_summarize

client = OpenAI(api_key=settings.OPENAI_KEY)


def num_tokens_from_messages(messages, model="gpt-3.5-turbo-0613"):
    """Return the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        print("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")
    if model in {
        "gpt-3.5-turbo-0613",
        "gpt-3.5-turbo-16k-0613",
        "gpt-4-0314",
        "gpt-4-32k-0314",
        "gpt-4-0613",
        "gpt-4-32k-0613",
    }:
        tokens_per_message = 3
        tokens_per_name = 1
    elif model == "gpt-3.5-turbo-0301":
        tokens_per_message = (
            4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
        )
        tokens_per_name = -1  # if there's a name, the role is omitted
    elif "gpt-3.5-turbo" in model:
        print(
            "Warning: gpt-3.5-turbo may update over time. Returning num tokens assuming gpt-3.5-turbo-0613."
        )
        return num_tokens_from_messages(messages, model="gpt-3.5-turbo-0613")
    elif "gpt-4" in model:
        print(
            "Warning: gpt-4 may update over time. Returning num tokens assuming gpt-4-0613."
        )
        return num_tokens_from_messages(messages, model="gpt-4-0613")
    else:
        raise NotImplementedError(
            f"""num_tokens_from_messages() is not implemented for model {model}. See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens."""
        )
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens


def cal_token_count(content_: str):
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo-16k-0613")

    token_count = len(encoding.encode(content_))
    # print(f"The text contains {token_count} tokens.")

    return token_count


class Ai:
    api_key = settings.OPENAI_KEY
    chatbot = None
    max_tokens = 16385
    tiktoken_divide_word = 3.5
    model = "gpt-3.5-turbo"

    def __init__(self):
        # self.chatbot = Chatbot(
        #     api_key=self.api_key,
        #     engine=self.model,
        #     max_tokens=self.max_tokens,
        # )
        pass

    def summarize(self, content_: str):
        if not content_:
            return ""
        # if num_tokens_from_messages(content_, self.model) > self.max_tokens:
        #     content_ = content_[0 : self.max_tokens]
        system_prompt = (
            "你的任务是阅读用户的输入，再组织输出总结，满足要求如下：\n    \n    "
            "1. 不管用户提供的是何种语言，都需要你以中文输出结果。\n    "
            "2. 用户将提供一些项目相关的介绍资料，资料以 markdown 格式呈现，你输出的总结内容可以拿来做项目简介，需要包含标题、项目介绍、项目特性等。\n    "
            "3. 你返回的整体文字总数在500字左右，不要输出英文。\n    "
            "4. 不要输出项目的捐赠、捐赠信息、捐款、赞助信息，贡献者、参与贡献者信息，鸣谢信息。\n    "
            "5. 不要输出原始html的 img a div 标签与内容。\n    "
            "6. 不要输出类似，总结内容约500字左右等你的总结信息。"
        )

        messages = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {"role": "user", "content": content_},
        ]

        response = self.ai_request(messages)
        response_message = response["choices"][0]["message"].to_dict()
        return response_message.get("content")

    def ai_request(self, messages):
        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=1,
            max_tokens=self.max_tokens - cal_token_count(json.dumps(messages)),
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )
        return response

    def summarize_in_sentences(self, content_: str):
        if not content_:
            return ""

        messages = [
            {
                "role": "system",
                "content": "阅读文字，将整个文本做一个总结，和提炼一个标题，输出时注意以下3点：\n"
                '1. 只能以合法的json格式返回数据给用户，{"title":"你总结的标题（符合中文表达习惯的内容）","summary":"符合上面要求的总结（符合中文表达习惯的内容）"}\n'
                "2. 其中的总结禁止分段分行输出，需要一整段输出，最好是3个句子。\n"
                "3. 输出内容的长度控制在100个汉字，禁止英文输出，使用中文输出。\n",
            },
            {"role": "user", "content": content_},
        ]
        response = self.ai_request(messages)

        response_message = response["choices"][0]["message"].to_dict()
        return response_message.get("content")

    def en_to_zh(self, content_: str):
        if not content_:
            return ""

        messages = [
            {
                "role": "system",
                "content": "你是一个科技文章的翻译人员，请翻译下面的文字，并保留markdown格式，尽量符合中文表达习惯。",
            },
            {"role": "user", "content": content_},
        ]
        response = self.ai_request(messages)
        response_message = response["choices"][0]["message"].to_dict()
        # print(response_message)
        return response_message.get("content")


class Streaming(StreamingStdOutCallbackHandler):
    result: str = ""

    def __init__(self):
        logging.info("start init callback")
        super().__init__()
        logging.info("end init callback")

    def on_llm_new_token(self, token, **kwargs):
        # it's not run to here
        logging.info(f"on llm new token，{token}")
        self.result += token
        # self.gen.send(token)

    def get_result(self):
        return self.result


def ai_handle(content: str):
    if not content:
        return None, None, None

    try:
        logging.info("translate...")
        # content_zh = Ai().en_to_zh(content)

        # streaming = Streaming()
        # langchain_translate(content, [streaming])
        # content_zh = streaming.get_result()

        content_zh = langchain_translate(content, None)
        # 图片域名替换
        content_zh = content_zh.replace("miro.medium.com", "auto.aimazing.site/medium")

    except Exception as e:
        error = traceback.format_exc()
        logging.exception("AI翻译出错")
        content_zh = "AI翻译出错，" + error

        return None, None, content_zh

    try:
        logging.info("summarizing...")
        # logging.info(content_zh)

        # streaming = Streaming()
        # langchain_summarize(content_zh, [streaming])
        # s_data = streaming.get_result()

        s_data = langchain_summarize(content_zh, None)
    except Exception as e:
        error = "AI总结出错" + traceback.format_exc()
        logging.exception("AI总结出错")
        return "error", error, content_zh

    try:
        j_data = json.loads(s_data)
        title = j_data.get("title")
        summary = j_data.get("summary")
    except Exception as e:
        error = "解析出错，AI 原始数据：" + s_data
        return "error", error, content_zh

    return title, summary, content_zh


if __name__ == "__main__":
    content = """
    
    <div align="center">
<img src="./docs/images/icon.svg" alt="预览"/>

<h1 align="center">ChatGPT Next Web</h1>

一键免费部署你的私人 ChatGPT 网页应用。

[演示 Demo](https://chat-gpt-next-web.vercel.app/) / [反馈 Issues](https://github.com/Yidadaa/ChatGPT-Next-Web/issues) / [加入 Discord](https://discord.gg/zrhvHCr79N) / [QQ 群](https://user-images.githubusercontent.com/16968934/228190818-7dd00845-e9b9-4363-97e5-44c507ac76da.jpeg) / [打赏开发者](https://user-images.githubusercontent.com/16968934/227772541-5bcd52d8-61b7-488c-a203-0330d8006e2b.jpg) / [Donate](#捐赠-donate-usdt)

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2FYidadaa%2FChatGPT-Next-Web&env=OPENAI_API_KEY&env=CODE&project-name=chatgpt-next-web&repository-name=ChatGPT-Next-Web)

[![Open in Gitpod](https://gitpod.io/button/open-in-gitpod.svg)](https://gitpod.io/#https://github.com/Yidadaa/ChatGPT-Next-Web)

![主界面](./docs/images/cover.png)

</div>

## 开始使用

1. 准备好你的 [OpenAI API Key](https://platform.openai.com/account/api-keys);
2. 点击右侧按钮开始部署：
   [![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2FYidadaa%2FChatGPT-Next-Web&env=OPENAI_API_KEY&env=CODE&project-name=chatgpt-next-web&repository-name=ChatGPT-Next-Web)，直接使用 Github 账号登录即可，记得在环境变量页填入 API Key 和[页面访问密码](#配置页面访问密码) CODE；
3. 部署完毕后，即可开始使用；
4. （可选）[绑定自定义域名](https://vercel.com/docs/concepts/projects/domains/add-a-domain)：Vercel 分配的域名 DNS 在某些区域被污染了，绑定自定义域名即可直连。

## 保持更新

如果你按照上述步骤一键部署了自己的项目，可能会发现总是提示“存在更新”的问题，这是由于 Vercel 会默认为你创建一个新项目而不是 fork 本项目，这会导致无法正确地检测更新。
推荐你按照下列步骤重新部署：

- 删除掉原先的仓库；
- 使用页面右上角的 fork 按钮，fork 本项目；
- 在 Vercel 重新选择并部署，[请查看详细教程](./docs/vercel-cn.md#如何新建项目)。

### 打开自动更新

> 如果你遇到了 Upstream Sync 执行错误，请手动 Sync Fork 一次！

当你 fork 项目之后，由于 Github 的限制，需要手动去你 fork 后的项目的 Actions 页面启用 Workflows，并启用 Upstream Sync Action，启用之后即可开启每小时定时自动更新：

![自动更新](./docs/images/enable-actions.jpg)

![启用自动更新](./docs/images/enable-actions-sync.jpg)

### 手动更新代码

如果你想让手动立即更新，可以查看 [Github 的文档](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/syncing-a-fork) 了解如何让 fork 的项目与上游代码同步。

你可以 star/watch 本项目或者 follow 作者来及时获得新功能更新通知。

## 配置页面访问密码

> 配置密码后，用户需要在设置页手动填写访问码才可以正常聊天，否则会通过消息提示未授权状态。

> **警告**：请务必将密码的位数设置得足够长，最好 7 位以上，否则[会被爆破](https://github.com/Yidadaa/ChatGPT-Next-Web/issues/518)。

本项目提供有限的权限控制功能，请在 Vercel 项目控制面板的环境变量页增加名为 `CODE` 的环境变量，值为用英文逗号分隔的自定义密码：

```
code1,code2,code3
```

增加或修改该环境变量后，请**重新部署**项目使改动生效。

## 环境变量

> 本项目大多数配置项都通过环境变量来设置，教程：[如何修改 Vercel 环境变量](./docs/vercel-cn.md)。

### `OPENAI_API_KEY` （必填项）

OpanAI 密钥，你在 openai 账户页面申请的 api key。

### `CODE` （可选）

访问密码，可选，可以使用逗号隔开多个密码。

**警告**：如果不填写此项，则任何人都可以直接使用你部署后的网站，可能会导致你的 token 被急速消耗完毕，建议填写此选项。

### `BASE_URL` （可选）

> Default: `https://api.openai.com`

> Examples: `http://your-openai-proxy.com`

OpenAI 接口代理 URL，如果你手动配置了 openai 接口代理，请填写此选项。

> 如果遇到 ssl 证书问题，请将 `BASE_URL` 的协议设置为 http。

### `OPENAI_ORG_ID` （可选）

指定 OpenAI 中的组织 ID。

### `HIDE_USER_API_KEY` （可选）

如果你不想让用户自行填入 API Key，将此环境变量设置为 1 即可。

### `DISABLE_GPT4` （可选）

如果你不想让用户使用 GPT-4，将此环境变量设置为 1 即可。

### `HIDE_BALANCE_QUERY` （可选）

如果你不想让用户查询余额，将此环境变量设置为 1 即可。

## 开发

点击下方按钮，开始二次开发：

[![Open in Gitpod](https://gitpod.io/button/open-in-gitpod.svg)](https://gitpod.io/#https://github.com/Yidadaa/ChatGPT-Next-Web)

在开始写代码之前，需要在项目根目录新建一个 `.env.local` 文件，里面填入环境变量：

```
OPENAI_API_KEY=<your api key here>

# 中国大陆用户，可以使用本项目自带的代理进行开发，你也可以自由选择其他代理地址
BASE_URL=https://chatgpt1.nextweb.fun/api/proxy
```

### 本地开发

1. 安装 nodejs 18 和 yarn，具体细节请询问 ChatGPT；
2. 执行 `yarn install && yarn dev` 即可。⚠️ 注意：此命令仅用于本地开发，不要用于部署！
3. 如果你想本地部署，请使用 `yarn install && yarn build && yarn start` 命令，你可以配合 pm2 来守护进程，防止被杀死，详情询问 ChatGPT。

## 部署

### 容器部署 （推荐）

> Docker 版本需要在 20 及其以上，否则会提示找不到镜像。

> ⚠️ 注意：docker 版本在大多数时间都会落后最新的版本 1 到 2 天，所以部署后会持续出现“存在更新”的提示，属于正常现象。

```shell
docker pull yidadaa/chatgpt-next-web

docker run -d -p 3000:3000 \
   -e OPENAI_API_KEY="sk-xxxx" \
   -e CODE="页面访问密码" \
   yidadaa/chatgpt-next-web
```

你也可以指定 proxy：

```shell
docker run -d -p 3000:3000 \
   -e OPENAI_API_KEY="sk-xxxx" \
   -e CODE="页面访问密码" \
   --net=host \
   -e PROXY_URL="http://127.0.0.1:7890" \
   yidadaa/chatgpt-next-web
```

如果你的本地代理需要账号密码，可以使用：

```shell
-e PROXY_URL="http://127.0.0.1:7890 user password"
```

如果你需要指定其他环境变量，请自行在上述命令中增加 `-e 环境变量=环境变量值` 来指定。

### 本地部署

在控制台运行下方命令：

```shell
bash <(curl -s https://raw.githubusercontent.com/Yidadaa/ChatGPT-Next-Web/main/scripts/setup.sh)
```

⚠️ 注意：如果你安装过程中遇到了问题，请使用 docker 部署。

## 鸣谢

### 捐赠者

> 见英文版。

### 贡献者

[见项目贡献者列表](https://github.com/Yidadaa/ChatGPT-Next-Web/graphs/contributors)

## 开源协议

[MIT](https://opensource.org/license/mit/)
    """

    content="""
    # OpenAI's o1 Model is Finally Here - A Model that Thinks Hard Before it Responds

![Image by [Jim Clyde Monge](None)](https://miro.medium.com/1*5OF855NaKh1xfa3PwaziVA.jpeg)

After months of teasing on social media and hiding behind the codename "[Project Strawberry](https://generativeai.pub/whats-with-sam-altman-s-strawberry-tweet-a-hint-to-gpt-5-release-88e57ced8fa2)," the highly anticipated new language [model](https://openai.com/index/introducing-openai-o1-preview/) from OpenAI is finally here - it's called '**o1**'.

It's a bit unconventional that they didn't name it GPT-5 or GPT-4.1. So, why did they go with o1?

According to OpenAI, the advancements in these new models are so significant that they felt the need to reset the counter back to 1:

> But for complex reasoning tasks this is a significant advancement and represents a new level of AI capability. Given this, we are resetting the counter back to 1 and naming this series OpenAI o1.

The main focus of these models is to **think and reason through complex tasks and solve harder problems**. So, don't expect it to be lightning-fast; instead, it delivers better and more logical answers than previous models.

The o1 family of models come in two variants: **o1-mini and the o1-preview.**

- **o1-preview:** This is model preview of the most advanced and most capable official o1 model that's to be released in the future. o1 significantly advances the state-of-the-art in AI reasoning.

- **o1-mini:** This is a faster, cheaper reasoning model that is particularly effective at coding. As a smaller model, o1-mini is 80% cheaper than o1-preview, making it a powerful, cost-effective model for applications that require reasoning but not broad world knowledge.

OpenAI emphasizes that these new models are trained with reinforcement learning to perform complex reasoning. But what exactly does reasoning mean in the context of LLMs?

### How Does Reasoning Work?

Much like how humans ponder for a while before answering a difficult question, o1 uses a **chain of thought** when attempting to solve a problem.

> It learns to recognize and correct its mistakes. It learns to break down tricky steps into simpler ones. It learns to try a different approach when the current one isn't working.

The key point is that reasoning allows the model to consider multiple approaches before generating final response.

**Here's the process:**

1. Generate reasoning tokens

2. Produce visible completion tokens as answer

3. Discard reasoning tokens from context

Discarding reasoning tokens keeps context focused on essential information.

![Image from OpenAI](https://miro.medium.com/0*F30rCHFGXooL-ssF.png)

> **Note:** While reasoning tokens are not visible via the API, they still occupy space in the model's context window and are billed as [output tokens](https://openai.com/pricing).

This approach may be slow but according to NVIDIA's senior researcher, Jim Fan, we are finally seeing the paradigm of inference-time scaling popularized and deployed in production.

![Image from Jim Fan](https://miro.medium.com/0*BdauKrF0NGbdjpfF)

Jim makes some excellent points:

1. **You don't need a huge model to perform reasoning.** Lots of parameters are dedicated to memorizing facts, in order to perform well in benchmarks like trivia QA. It is possible to factor out reasoning from knowledge, i.e. a small "reasoning core" that knows how to call tools like browser and code verifier. Pre-training compute may be decreased.

2. **A huge amount of compute is shifted to serving inference instead of pre/post-training.** LLMs are text-based simulators. By rolling out many possible strategies and scenarios in the simulator, the model will eventually converge to good solutions. The process is a well-studied problem like AlphaGo's monte carlo tree search (MCTS).

### How Does o1 Compare to GPT-4o?

To test how o1 models stack up against GPT-4o, OpenAI performed a diverse set of human exams and ML benchmarks.

![Image from OpenAI](https://miro.medium.com/1*BTydTfMF9dRHv3YSrkhSjg.png)

The graph above demonstrates that o1 greatly improves over GPT-4o on challenging reasoning benchmarks involving math, coding, and science questions.

In evaluating OpenAI's newly released o1 models, OpenAI discovered that they excel on the GPQA-diamond benchmark - a challenging intelligence test that assesses expertise in chemistry, physics, and biology.

To compare the model's performance to that of humans, OpenAI collaborated with experts holding PhDs who answered the same GPQA-diamond questions.

Remarkably, o1 surpassed these human experts, becoming the first model to do so on this benchmark. While this doesn't imply that o1 is superior to a PhD in all respects, it does indicate that the model is more proficient in solving certain problems that a PhD would be expected to solve.

You can read more about the technical report of o1 models [here](https://openai.com/index/learning-to-reason-with-llms/).

---

Now, to see how well o1 performs compared to the previous model, GPT-4o, let's look at a classic problem: counting the number of 'r's in the word "strawberry."

> Prompt: How many 'r' letter are in the word strawberry?

![](https://miro.medium.com/1*IDi8OxtftoM4PHqWE9G-WQ.png)

- o1 took 33 seconds and 296 tokens to solve it, answering correctly.

- GPT-4o took less than a second, consumed 39 tokens, but failed the test.

Let's try another one. This time, we'll ask both models to come up with a list of countries with the letter 'A' in the third position in their names.

> Prompt: Give me 5 countries with letter A in the third position in the name

![Image by [Jim Clyde Monge](None)](https://miro.medium.com/1*ubYLGTIb7gHVUxkweKeb9w.png)

Again, o1 answered correctly, despite taking longer to 'think' than GPT-4o.

### o1 is Not Perfect

Even Sam Altman acknowledged that o1 is still flawed and limited. It might seem more impressive on first use than it does after you spend more time with it.

<iframe src="https://cdn.embedly.com/widgets/media.html?type=text%2Fhtml&key=d04bfffea46d4aeda930ec88cc64b87c&schema=twitter&url=https%3A//x.com/sama/status/1834283100639297910&image=" title="" height="281" width="500"></iframe>

Sometimes, it can still make mistakes - even on simple questions like asking how many 'r's are in its response.

![Image by [Jim Clyde Monge](None)](https://miro.medium.com/0*QeqqWodboj5TPVnB)

Another thing to note is that o1 models offer significant advancements in reasoning but are **not intended to replace GPT-4o in all use cases.**

For applications that need image inputs, function calling, or consistently fast response times, the GPT-4o and GPT-4o mini models will continue to be the right choice.

For developers, here are some of o1's chat completion API parameters that are not yet available:

- **Modalities**: text only, images are not supported.

- **Message types**: user and assistant messages only, system messages are not supported.

- **Streaming**: not supported.

- **Tools**: tools, function calling, and response format parameters are not supported.

- **Logprobs**: not supported.

- **Other**: `temperature`, `top_p` and `n` are fixed at `1`, while `presence_penalty` and `frequency_penalty` are fixed at `0`.

- **Assistants and Batch**: these models are not supported in the Assistants API or Batch API.

### How to Get Access to o1 Model?

o1 is rolling out today in ChatGPT to all Plus and Team users, and in the API for developers on tier 5.

If you're a free ChatGPT user, OpenAI mentioned that they're planning to bring o1-mini access to all ChatGPT Free users, but no specific schedule was provided.

o1 is also available in the OpenAI Playground. Just login to [https://platform.openai.com/](https://platform.openai.com/) and under the Playground tab, set the model to either "o1-mini" or "o1-preview".

![Image by [Jim Clyde Monge](None)](https://miro.medium.com/1*OPHxvFd4hJhOMNC0iZUcGA.png)

There's also the API models "o1-mini-2024–09–12" and the "o1-preview-2024–09–12" which are already accessible to developers.

### Prompting Tips for o1 Models

If you're used to your usual prompting with models like Claude 3.5 Sonnet, Gemini Pro, or GPT-4o, prompting o1 models is different.

o1 models perform best with straightforward prompts. Some prompt engineering techniques, like few-shot prompting or instructing the model to "think step by step," may not enhance performance and can sometimes hinder it.

Check out some best practices:

- **Keep prompts simple and direct:** The models excel at understanding and responding to brief, clear instructions without the need for extensive guidance.

- **Avoid chain-of-thought prompts:** Since these models perform reasoning internally, prompting them to "think step by step" or "explain your reasoning" is unnecessary.

- **Use delimiters for clarity:** Use delimiters like triple quotation marks, XML tags, or section titles to clearly indicate distinct parts of the input, helping the model interpret different sections appropriately.

- **Limit additional context in retrieval-augmented generation (RAG):** When providing additional context or documents, include only the most relevant information to prevent the model from overcomplicating its response.

---

### Final Thoughts

Okay, so o1 is impressive when it comes to chat-based problem-solving and content generation. But do you know what I'm most excited about? Its integration into coding assistants like [Cursor AI](https://generativeai.pub/8-year-old-kids-can-now-builds-apps-with-the-help-of-ai-118122d1f226).

I've already seen folks plugging in their API keys into Cursor and using o1 to write code for them. I haven't tried it yet, but I'm super excited to give it a go.

From my initial tests, o1's ability to think, plan, and execute is off the charts. We're basically witnessing a ChatGPT moment for agentic coding systems. The implications of its new capabilities are immense.

I genuinely believe that the wave of brand-new products that will be built with this will be unlike anything we've ever seen. The new possibilities in the world of software development are thrilling, and I can't wait to see how o1 will revolutionize the way we code and build applications in the coming weeks.

![](https://miro.medium.com/0*6yLyHPUmfW6MNH9P.png)

This story is published on [Generative AI](https://generativeai.pub/). Connect with us on [LinkedIn](https://www.linkedin.com/company/generative-ai-publication) and follow [Zeniteq](https://www.zeniteq.com/) to stay in the loop with the latest AI stories.

Subscribe to our [newsletter](https://www.generativeaipub.com/) and [YouTube](https://www.youtube.com/@generativeaipub) channel to stay updated with the latest news and updates on generative AI. Let's shape the future of AI together!

![](https://miro.medium.com/0*0WfTvugMhfFfyWUK.png)

    
    
    """
    print(len(content))
    # result = Ai().summarize(content)
    result = ai_handle(content)
    print(result)
