import datetime
from datetime import datetime

from langchain import LLMChain
from langchain.chains.summarize import load_summarize_chain
from langchain.chat_models import ChatOpenAI
from langchain.prompts import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    ChatPromptTemplate,
)
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

from app.providers.ai import cal_token_count
from config.config import settings

#
# url = "https://medium2.p.rapidapi.com/article/49bde224f43c/markdown"
#
# headers = {
#     "X-RapidAPI-Key": "07a05c759fmshd0cd5e0712bed8ap19e6a0jsn8c3d0b8d1654",
#     "X-RapidAPI-Host": "medium2.p.rapidapi.com",
# }
#
# response = requests.get(url, headers=headers)
# data = response.json()

text = """
# How To Build an Email Validation Service Business (Full Guide)\n\nToday we will go on a new entrepreneurial journey to understand how to build a full-scale online business.\n\nI've picked up **\" Email Validation Service Business** \".\n\nThis will be more exciting than you think. And Guess What! **ChatGPT Will Help us in almost every step!**\n\n![](https://miro.medium.com/0*l8Sm8NmkpY5MWKf3.gif)\n\n### What is an Email Validation Service Business?\n\nImagine having a party and sending out invites to all your friends. But alas, half the invitations bounce back because you jotted down the wrong addresses.\n\n**Bummer, right?** Now, replace this scenario with businesses sending out emails to customers. We wouldn't want the same problem there!\n\nThat's where an Email Validation Service comes in like a superhero! **It's a service that verifies email addresses are legit before businesses hit that ‘send' button.**\n\nIt is more than just avoiding undelivered emails. It's about maintaining a **high sender reputation, improving email deliverability, reducing bounce rates, and more**. It's about ensuring that your business's emails reach people's inboxes, not their spam folders!\n\nSounds like an awesome business idea, doesn't it?\n\nThat's because it is! **and the cool part, AI will not take over soon!**\n\n![](https://miro.medium.com/0*JHo_9NqFWLF8P6NI.png)\n\nEver heard of **ZeroBounce, [Debounce](https://learnwithhasan.com/refer/debounce), or NeverBounce**?\n\nThose are an example of Email Validation Services. It is a **SAAS-based business Model** where users pay a monthly subscription or buy credits to validate emails.\n\nToday, I will walk you through how we can build something similar, starting from scratch and passing by all the technical details-and sharing with you **three different Methods** of building this Service, monetization, and how I built my own [email validation service](https://promoterkit.com/tools/email/bulk-verifier). And much more!\n\nLet's proceed to the fun part - **naming your business!**\n\n### Choosing a Name for Your Business\n\nNaming your business can feel like naming your pet turtle - you want it to be fun, unique, and a bit descriptive of its personality. And just like you wouldn't want your turtle to share its name with every other turtle in the neighborhood, **your business name must also stand out!**\n\nBut don't worry. You've got ChatGPT by your side, and it's as good at naming businesses as it is at pretty much everything else. You have to ask it.\n\nFor example, you could say:\n\n```perl\nI need a cool name for my Email Validation Service business,\" and it'll churn out some creative options like \"SureMail,\" \"BounceZapper,\" or \"InboxAssure.\"\n```\n\n![](https://miro.medium.com/0*NRchYoMWNZ3lhgoW.gif)\n\nBut let's be more professional. Let's ask ChatGPT The right way!\n\nHere is an optimized prompt template to generate domain names with ChatGPT:\n\n```vbnet\nPlease generate 10 original and creative domain names specifically tailored for the [niche] niche, focusing on its main concepts and target audience. Your response should prioritize domain names that effectively capture the attention of the [niche] audience and represent its key themes. For each domain name, provide a brief explanation (1-2 sentences) highlighting its relevance to the niche. Ensure that each domain name meets the following criteria: 1. Brand Relevance: Maintain a strong connection with the niche and its central concepts. 2. Memorable: Design the domain names to be captivating, easy to remember, and with familiar spellings. 3. Concise: Keep each domain name between 6-14 characters for ease of typing and recall. 4. Simplicity: Avoid using hyphens and numbers for a cleaner appearance. 5. Keyword Incorporation: Utilize relevant niche keywords for improved SEO, if possible. 6. Pronunciation: Ensure that each domain name is easily understandable when spoken or \"radio-friendly.\" 7. Domain Extensions: Prioritize .com, .net, .org, and .ai extensions when applicable. 8. Legality: Refrain from infringing on existing trademarks or brands. Your response should exhibit flexibility and creativity while maintaining a focused approach on the [niche] niche, providing a solid foundation for building a brand within that market.[niche]:\n```\n\n_Note: This prompt is part of our [premium prompts library](https://learnwithhasan.com/premium-prompt-library/)._\n\nOnce you have a few names in mind, it's time to pick your favorite. Make sure it's catchy, easy to remember, and gives an idea of your business.\n\nNow that we've got our name, let's jump into understanding how email validation works. Are you ready?\n\n### How does Email Validation Work?\n\nYou know how in video games, you have to pass various levels to reach the ultimate boss battle? Well, email validation works similarly - in three levels. Let's break down this epic ‘game':\n\n1. **Level One - Syntax Validation:** This is the first checkpoint where we make sure the email addresses look like, well, email addresses. Does it have an ‘@'? Is there a period followed by a domain extension, like ‘.com' or ‘.net'? If the email address is something like ‘John Doe @ nowhere', our syntax validation will give it a big thumbs down.\n\n2. **Level Two - DNS MX Validation:** Here, we're checking if the domain of the email address actually exists. So if someone enters an email address with ‘@**imaginaryplace.com**', at this level, the validation service will cry foul 😅 \n\n3. **Level Three - Mailbox Validation:** Now, this is the ultimate boss battle. This level checks whether the mailbox really exists within the domain. Think of it as confirming if there's really a guy named John at ‘[[email protected] ](https://learnwithhasan.com/cdn-cgi/l/email-protection#1b717473755b697e7a776b777a787e35787476)‘. This is the toughest and most important level to crack.\n\n![](https://miro.medium.com/0*yFqf8W4-xq-96NQX.png)\n\nSo, now you understand the basics of how an email validation service works. Next, we will explore the methods to build one.\n\n### Three Methods To Build an Email Validation Service\n\nWe've three options to build our email validation service.\n\n1. **Buy a Script:** This is like getting a ready-to-assemble kit. You buy it, put the pieces together, add a bit of personal flair, and voila, you have your business. You could be up and running in just a few hours! This one is Simple, Fast, and Affordable **BUT** **Hard To Maintain and Scale**\n\n2. **Build on Top of Another API:** This method is like standing on the shoulders of a giant (a friendly one, of course). You use an existing service, like the affordable and powerful Debounce API, as your foundation and build your email validation service on top of it.\n\n3. **Build It Yourself (Advanced):** This path is for the brave and tech-savvy amongst you. You are the one who likes to build LEGO sets without instructions. It's a challenging route but gives you the most control and customization.\n\nI will cover all three routes in this Guide in a way you don't need any other post, course, or guide to read.\n\n### Method 1: Buy an Email Validation Script\n\nThis is the easiest approach. It is simply finding a ready-made script that you publish online in a couple of hours. **And Run Your Business.**\n\nI did my Homework, searched for an email validation service script, and found one.\n\nIt is called the \"**[Email Verifier Pro](https://learnwithhasan.com/refer/email-verifier-pro)**\" and I found it on [Codecanyon](https://learnwithhasan.com/refer/codecanyon).\n\nBy the way, codecanyon is a great place to find many scripts to start a business with. I did this several times, and today, I run [Large File Sender](https://largefilesender.com/), which is a script I bought from codecanyon.\n\nAnyway, the idea is you buy the script, host, and configure it. And you are ready!\n\nI am not here to promote the script, or so, but the idea of getting a script from codecanyon, rebranding it, and lunch, works well in many case scenarios, especially in a Growth Marketing strategy called starting a Tool Site as a side project.\n\n### BUT! There are a few things you need to consider here.\n\nAs someone who bought more than 50 Scripts from codecanyon and has been testing this method for more than 4 years, I want to share with you some important points and downsides that you must know before taking any action and investing in such scripts and projects.\n\n**1. Rebranding**\n\nSince this script is available for sale publicly, and anyone can buy it, it is obvious that you should rebrand the whole website to look unique. Otherwise, it will look weird that 100 websites running the same business with the same design under different names.\n\nSo you should work on rebranding your script. And this requires some HTML-CSS-JS Skills. or Hiring someone to do it for you.\n\n**2. Technical Support**\n\nUsually, you get support whenever you buy a script from codecanyon, but the problem is that this support is limited, and you don't have control over all the features and technical stuff behind the script, especially in our case, \"Email validation\" I think support and maintenance are very important as you will see later when we discuss how these services work.\n\n3. **Updates**\n\nLike support, and like any website or service, it requires updates, and this will be all depended on the script author.\n\n[🟥 ](https://emojipedia.org/large-red-square/)I**f you want my honest opinion,** I don't prefer this method in the case of email validation service business. Maybe in something else and more simple, it is a good choice.\n\n### Method 2: Build on Top of an API\n\nOkay, so this method is a bit like playing a video game with a cheat code. Instead of starting from scratch, you're building on something already existing.\n\nIn this case, we're talking about APIs (Application Programming Interfaces) - they're like cheat codes for programming.\n\nFor our email validation service, we could use an API from a reliable service like **[Debounce](https://learnwithhasan.com/refer/debounce)**.\n\nHere, you'll create a Python script that calls on Debounce's API to validate emails. And to make things even cooler, you could implement caching to save API calls and cut costs.\n\nYou could even use a database like PostgreSQL or MySQL for scaling. But remember, this path requires a bit of programming knowledge. However, don't worry. We're all in this together, and with ChatGPT, no challenge is too big.\n\nYou can ask ChatGPT to write a Python script for you. You can use a [power prompt](https://learnwithhasan.com/premium-prompt-library/) like this one:\n\n```vbnet\nAs a seasoned Python programmer with 20 years of experience working with a diverse range of individuals, your responsibility encompasses not only writing Python scripts based on user needs, but also asking clarifying questions before formulating responses or offering solutions. Your main task is to help me create a Python script tailored to my needs. Before you proceed with your response or solution, please ensure you ask relevant questions that would help you thoroughly understand what I am seeking - my goals, the desired output, the specific problem I am trying to solve, and any constraints I might have. In addition to interpreting my request, in case you find opportunities for optimizing my reasoning or the overall goal, bring them to my attention. Explain why the proposed optimization would be beneficial, and how it would affect the outcome of the task. To avoid misunderstanding, restate the question or task back to me to confirm you have fully understood my requirements. Is this guide clearly understood?\n```\n\nAnd here is the script that you can use:\n\n```python\nimport requests\ndef validate_email(email): \n  api_key = 'your_debounce_api_key' \n  response = requests.get(f'https://api.debounce.io/v1/?api={api_key}&email={email}') \n  result = response.json() \n  return result['debounce']['result'] \n# Use the function print(validate_email('[email protected]'))\n```\n\nReplace `'your_debounce_api_key'` with your actual [Debounce API](https://learnwithhasan.com/refer/debounce) key and `'[[email protected]](https://learnwithhasan.com/cdn-cgi/l/email-protection)'` With the email, you want to validate. This script sends a request to the Debounce API and gets a response, which tells you if the email is valid or not.\n\nNow, let's add caching to this script to save API calls and cut costs. We'll use a simple dictionary as a cache in this example, but you can replace it with a more sophisticated cache or a database in a real-world application:\n\n```python\nimport requests\ncache = dict() \ndef validate_email(email): \n  if email in cache: \n    return cache[email] \n  api_key = 'your_debounce_api_key' \n  response = requests.get(f'https://api.debounce.io/v1/?api={api_key}&email={email}') \n  result = response.json() \n  # Save result in cache \n  cache[email] = result['debounce']['result'] \n  return result['debounce']['result'] # Use the function print(validate_email('[email protected]'))\n```\n\nNext, let's discuss how to turn this business into a money-making machine. Are you ready to find out?\n\n### How To Monetize?\n\nBefore we move on to Method 3, which is the most complicated, **let's talk about money!**\n\nOkay, we've built our cool Email Validation Service. Now, let's turn it into our money-making machine! We have three main ways to do that:\n\n1. **Free Tool:** You could offer your service as a free tool. Just like I did with my tool, [PromoterKit Email Validation](https://promoterkit.com/tools/email/bulk-verifier). Now, you might be thinking, \"Wait, how do I make money if it's free?\" Well, ever seen those billboards on highways? They're free to look at, but the companies advertising on them are paying for that space. You can do the same with your service - **sell ad spaces!** Or maybe affiliate with email validation services to make some commissions! their tools also are super important when it comes to growing online. You can get a lot of traffic, build email lists, and prompt your premium services! [Check this guide for more details](https://medium.com/real-marketing/my-plan-to-reach-5-000-000-page-views-per-month-in-2023-85c2082062fc?source=your_stories_page-------------------------------------).\n\n2. **SAAS Model:** This is like a gym membership. People pay you a monthly fee (subscription) or buy credits to use your service. This model can provide a steady flow of income and is especially effective if you can demonstrate ongoing value to your users.\n\n3. **Sell as An API:** You could also go wholesale and [sell your service as an API](https://learnwithhasan.com/build-api-no-code-tools/) on platforms like RapidAPI. This way, other businesses can use your email validation service as part of their apps and services. If you like to go into more detail, you can check out [my full course on How to build and Sell APIs here.](https://learnwithhasan.com/build-sell-api-course-waiting-list/)\n\n![](https://miro.medium.com/0*YPdH6lLnQZzij_oo.png)\n\nAlright, we're nearly there! Let's move on to the more technical part - building our own Email Validation Service. Ready for the challenge?\n\n### The Advanced Method: Building Your Own Email Validation Service\n\nIf you're a fan of LEGO and love creating magnificent structures from those little bricks, then this is for you. We're going to build our Email Validation Service from scratch!\n\nNow, remember those three levels of email validation we discussed earlier? We're going to implement those. Here's a basic prototype of how this might look in Python. Again you can use ChatGPT and here is the output:\n\n```python\nimport re\nimport dns.resolver\nimport smtplib\n\ndef validate_email(email):\n    # Level 1: Syntax validation\n    if not re.match(r\"[^@]+@[^@]+\\.[^@]+\", email):\n        return 'Invalid syntax'\n    \n    domain = email.split('@')[1]\n    \n    # Level 2: DNS MX validation\n    try:\n        dns.resolver.resolve(domain, 'MX')\n    except dns.resolver.NXDOMAIN:\n        return 'Invalid domain'\n    \n    # Level 3: Mailbox validation (requires a valid SMTP server on your end)\n    server = smtplib.SMTP('your_smtp_server')\n    response = server.verify(email)\n    server.quit()\n    \n    if response[0] != 250:\n        return 'Invalid mailbox'\n    \n    return 'Valid email'\n```\n\nBuilding your own service gives you the most control over the process and allows for advanced features like bulk validation, real-time validation, and more. However, it's also the most challenging route and requires a good understanding of email systems and server administration. But hey, we're here for a challenge, right?\n\n![](https://miro.medium.com/0*oH1frs3TRb5P2blC.gif)\n\nBuilding a large-scale Email Validation Service like DeBounce or NeverBounce requires a bit more planning and technical expertise, but it's certainly a rewarding venture. Here's a step-by-step process:\n\n### Step 1: Design a Robust Architecture\n\nYour service needs to be able to handle a large volume of requests efficiently. For this, consider using a cloud provider like AWS, Google Cloud, Digital Ocean, or Azure. They offer scalable solutions like serverless functions (AWS Lambda, Google Cloud Functions, etc.), which can efficiently handle varying loads.\n\n### Step 2: Implement Multi-Level Email Validation\n\nAs we've discussed before, email validation has three levels. You'll need to implement each of them:\n\n**Syntax Validation**\n\nThis is straightforward and can be implemented using a regular expression to check if the email has a valid format.\n\n**DNS MX Record Validation**\n\nYou'll need to query the DNS MX records of the domain part of the email address. This tells you if the domain is configured to receive emails. Python's `dns.resolver` module can help with this.\n\n**SMTP Mailbox Validation**\n\nThis is the trickiest part. To verify if the mailbox exists, you must initiate a connection with the SMTP server of the email's domain. This is often done using the \"RCPT TO\" command.\n\nHowever, some SMTP servers are always configured to return a successful response to prevent spammers from validating emails, a configuration known as a \"catch-all\" server. Dealing with this requires more complex logic, like sending multiple validation emails at different times and analyzing the response patterns.\n\nMoreover, due to the potential for misuse, many SMTP servers use anti-spam techniques like greylisting, which will temporarily block your IP. **It's crucial to implement a retry mechanism and handle these situations gracefully.**\n\nDealing with IP blacklisting and blockage is an important consideration when building an Email Validation Service. When you're frequently making SMTP connections for validation, there's a risk that your IP could get blacklisted by anti-spam systems.\n\nHere are some strategies to tackle this issue:\n\n1. **IP Rotation:** This involves using a pool of IP addresses rather than a single one. If one IP gets blacklisted, you can switch to another. There are cloud services available that offer IP rotation.\n\n2. **Slow Down Your Requests:** Making too many requests in a short time span can lead to your IP being considered as spam. Implement a rate limit to slow down your requests.\n\n3. **Respect \"Greylisting\":** Some servers temporarily reject mail from an unknown sender/ IP (this is known as greylisting). In such cases, the server sends a specific response that means \"try again later\". Ensure your service recognizes this response and appropriately retries after a delay.\n\n4. **Authenticate Your Email:** Implementing SPF (Sender Policy Framework), DKIM (DomainKeys Identified Mail), and DMARC (Domain-based Message Authentication, Reporting & Conformance) will help your IP gain a good sending reputation.\n\n5. **Maintain Good List Hygiene:** Regularly clean up your email list to avoid repeatedly sending validation requests to bad addresses, which can harm your reputation. (this is why caching is important)\n\nRemember, blacklisting can seriously impact the effectiveness of your service, so it's essential to monitor your IP reputation and take corrective action if you notice issues.\n\n### **Step 3: Ensure Fast Response Times**\n\nTo ensure a smooth user experience, you need fast response times. This can be a challenge because SMTP connections can be slow. Consider using techniques like:\n\n### Caching\n\nStore the results of previous validations and use them for repeated requests. This can significantly improve response times and reduce the load on your servers.\n\n### Concurrent Validations\n\nPerform multiple validations concurrently instead of one-by-one. This can be achieved with multithreading or asynchronous programming.\n\n### Step 4: Implement Bulk Validation\n\nLarge-scale email validation services often need to validate lists of emails at once. Implementing this requires being able to accept a list of emails, validate them concurrently, and return the results in a convenient format, such as a CSV file.\n\n### Step 5: Ensure Privacy and Security\n\nEmail addresses are sensitive data, and your service must handle them securely. Implement strong encryption for data at rest and in transit, and ensure your service is compliant with relevant regulations like GDPR.\n\nThis is a challenging project, but with a step-by-step approach and the right tools, it's certainly achievable. I hope this guide helps you get started on building your own large-scale Email Validation Service!\n\nNeed More Help? I am here to help and discuss any related issues. [Join us on the forum.](https://learnwithhasan.com/forum/)\n\n### Create the UI for your scripts.\n\nSo, we've built this amazing Email Validation Service. Now, let's dress it up with an awesome user interface! It's like setting up your room - you want it to look appealing and feel comfortable.\n\nHere are some ways you can create a stunning UI:\n\n1. **Develop it Yourself or Hire a Programmer:** If you're at home in the world of HTML, CSS, and JavaScript, or have a tech-savvy buddy who owes you a favor, this might be your route. It's like customizing your room yourself!\n\n2. **Use No-Code Tools like Bubble:** If the thought of coding makes you break out in a cold sweat, don't worry! No-code tools like Bubble can help you design a beautiful UI without typing a single line of code. It's like having an interior designer set up your room! You can also AI-powered Tools Like [Builder](https://www.builder.ai/) and [Framer](https://www.framer.com/)\n\n3. **Use Semi No-Code Tools like [Anvil](https://anvil.works/):** If you're not afraid of a bit of coding and want more control, semi no-code tools like Anvil might be the answer. It's a middle ground, like setting up your room with some professional help.\n\n4. **Build with ChatGPT using a Power Prompt:** Believe it or not, ChatGPT is more than just a pretty AI face. It can help you build a simple UI with a well-crafted power prompt.\n\nHere is a UI ChatGPT Created for me:\n\n![](https://miro.medium.com/0*RGkORpS6bYVdzWnP.png)\n\nYou can download the [source code here](https://learnwithhasan.com/?sdm_process_download=1&download_id=4430).\n\nRemember, your UI is the first thing your users see when they visit your service. Make it inviting, easy to use, and reflective of your brand. Ready for the next step? Let's get your business up and running!\n\n### Lunch Your Business 🚀 \n\nCreating your Email Validation Service is like building a shiny new spaceship, but now you've got to launch it into the cosmos. So, how can we make a successful launch? Here are some tips:\n\n**Test Everything:** Before you launch, make sure everything is working as expected. You know how they do pre-flight checks before a rocket launch? Do the same for your business. Test all features, especially the user experience.\n\n**Publish on Product Hunt:** Known as a launching pad for many successful start-ups, Product Hunt is a must-visit platform when introducing your online business to the world. It's a daily showcase for new products and businesses where you can present yours to a community of tech enthusiasts and potential customers. Make your submission engaging with high-quality images, a compelling tagline, and a clear, concise description of what your business offers. Stay active during the launch day to answer questions and engage with the community.\n\n**Leverage Medium and Twitter:** In addition to your business's blog or website, consider utilizing platforms like Medium and Twitter for promotion. Medium's network offers exposure to a wide audience that may be interested in your business. You can publish articles related to your product or industry, providing valuable insights that can help establish your business as a thought leader in the field.\n\nTwitter, on the other hand, is a real-time social network that allows you to engage with your customers directly. Use this platform to share updates, news, and promotions about your business, as well as to provide timely customer service. Twitter's hashtag system can also be used to increase the visibility of your tweets to users interested in your industry or product.\n\n**Optimize for Search Engines (SEO):** Lastly, but no less critical, is optimizing your online presence for search engines. SEO, or Search Engine Optimization, involves structuring your website and content in such a way that it ranks high in search engine results for relevant queries.\n\nLet me reveal another power prompt that will help you craft an SEO Content Strategy:\n\n```\nYour task as an English-speaking SEO market research professional is to develop a comprehensive SEO content strategy plan based on a specific keyword. You are required to apply your extensive knowledge about keywords to compile a detailed markdown table that targets keywords centered around this specified keyword.\n\nYour table should encompass five columns: Keyword Cluster, Long-Tail Keyword,  Search Intent, Title, and Meta Description. Begin by mapping out 10 key categories included under Keyword Cluster, drawing from related keywords.\n\nIn the Search Intent column, specify the searcher's primary intent for each keyword, categorizing the topic as either Commercial, Transactional, or Informational. Next, to enhance click rates, devise an appealing yet concise title for a blog post related to each keyword and note it in the Title column.\n\nIn the Meta Description column, craft an engaging summary of up to 155 words that accentuates the article's value and includes a compelling call to action to entice the searcher to click. Avoid generic phrases such as ‘introduction', ‘conclusion', or ‘tl:dr' and focus exclusively on the most specific and relevant keywords.\n\nPlease refrain from using quotes or any other enclosing characters within columns. Also, your entire table and all responses should be in fluent English. Begin your task with the provided keyword: [keyword].\n```\n\nRemember, SEO is not a one-time task, but an ongoing effort. Search engine algorithms are always changing, and staying up-to-date with the latest practices will help your online business maintain its visibility.\n\nAnd that's it! You're ready to make your mark in the Email Validation Service world. The principles we've covered here can work with any business idea you have. So, whether you're launching a space shuttle or starting a lemonade stand, you now have the knowledge to make it happen!\n\n## 🟥Master the Most In-Demand Skill of the Future!\n\nEnroll in the ‘ **Become a Prompt Engineer**' program. We'll take you from novice to expert in scripting AI workflows. [Start your journey here!](https://learnwithhasan.com/prompt-engineering-course/?utm_source=blog&utm_medium=blog_post&utm_content=cta_bottom)\n\n![](https://miro.medium.com/0*PWj_vEDszxaNC76n.jpeg)\n\n### What Will You Get?\n\n- Access to our premium Prompt Engineering Course\n\n- Access our private support forum to get help along your journey.\n\n- Access to our Premium Tested Prompts Library.\n\n---\n\n_Originally published at [https://learnwithhasan.com](https://learnwithhasan.com/build-email-validation-service-business/) on July 18, 2023._
"""

data = {"markdown": text}

markdown = data.get("markdown")
print(len(text))

# translate

# url = "https://deep-translate1.p.rapidapi.com/language/translate/v2"
#
# payload = {"q": markdown, "source": "en", "target": "zh_CN"}
# headers = {
#     "content-type": "application/json",
#     "X-RapidAPI-Key": "07a05c759fmshd0cd5e0712bed8ap19e6a0jsn8c3d0b8d1654",
#     "X-RapidAPI-Host": "deep-translate1.p.rapidapi.com",
# }
#
# response = requests.post(url, json=payload, headers=headers)
#
# data = response.json()
# print(data.get("data").get("translations").get("translatedText"))

# url = "http://18.136.226.169:1188/translate"
# payload = {"text": markdown, "source_lang": "EN", "target_lang": "ZH"}

# response = requests.post(url, json=payload)

# translator = Translator("")
# print(translator.en_to_zh(text))
# print(response.text)

# print(requests.get("https://api.ipify.org").text)
# deepl 测试版本
# import deepl
# auth_key = ""  # Replace with your key
# translator = deepl.Translator(auth_key)
# print(len(text), cal_token_count(text), len(text) / cal_token_count(text))
print(datetime.now())
# print(Ai().summarize_in_sentences(text))
print(cal_token_count(text))
print(datetime.now())
# result = translator.translate_text(text=text, target_lang="ZH")
# print(result.text)


def langchain_test(content: str):
    # 初始化文本分割器
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=0)

    # 切分文本
    split_chunks = text_splitter.split_text(content)
    print(f"chunks:{len(split_chunks)}")

    # 加载 llm 模型
    llm = ChatOpenAI(model_name="gpt-3.5-turbo-16k", max_tokens=1500)

    docs = [Document(page_content=t) for t in split_chunks]

    # 创建总结链
    chain = load_summarize_chain(llm, chain_type="refine", verbose=True)

    # 执行总结链，（为了快速演示，只总结前5段）
    result = chain.run(docs)

    print(result)


def langchain_chat(system_message: str, content: str):
    # 初始化文本分割器
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=16000, chunk_overlap=10)

    # 切分文本
    split_chunks = text_splitter.split_text(content)
    for a in split_chunks:
        print(a)
        print("==============================================================")
    print(f"chunks:{len(split_chunks)}")

    system_message_prompt = SystemMessagePromptTemplate.from_template(system_message)

    human_template = "{text}"
    human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

    chat_prompt = ChatPromptTemplate.from_messages(
        [system_message_prompt, human_message_prompt]
    )

    # 加载 llm 模型
    llm = ChatOpenAI(model_name="gpt-3.5-turbo-16k-0613")

    llm_chain = LLMChain(llm=llm, prompt=chat_prompt)

    print(datetime.now())
    input_list = [{"text": t} for t in split_chunks]
    result = llm_chain.apply(input_list)
    print(datetime.now())

    # result = llm_chain.generate(input_list)
    print(result)
    # print(result[0]["text"])

    ret = ""
    for r in result:
        ret += r.get("text")

    return ret


def langchain_translate(content: str):
    system_message = "You are a helpful assistant that translates English to Chinese. and keep the markdown format."
    return langchain_chat(system_message, content)


def langchain_summarize(content: str):
    system_message = """
    Write a concise summary of the following, and output the JSON data. The JSON data structure is as follows:

    {{"title": "Extracted content title in Chinese", "summary": "Summarized content that not more than 300 words in Chinese"}}

    the value of json data is in Chinese, not in English.
    """
    return langchain_chat(system_message, content)


def langchain_test2(content: str):
    # 初始化文本分割器
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=16000, chunk_overlap=10)

    # 切分文本
    split_chunks = text_splitter.split_text(content)
    for a in split_chunks:
        print(a)
        print("==============================================================")
    print(f"chunks:{len(split_chunks)}")

    template = "You are a helpful assistant that translates English to Chinese. and keep the markdown format."
    system_message_prompt = SystemMessagePromptTemplate.from_template(template)

    human_template = "{text}"
    human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

    chat_prompt = ChatPromptTemplate.from_messages(
        [system_message_prompt, human_message_prompt]
    )

    # get a chat completion from the formatted messages
    # send_p = chat_prompt.format_prompt(
    #     input_language="English", output_language="Chinese", text="I love programming."
    # ).to_messages()

    # and extract and summarize the translated content, and output the JSON data. The JSON data structure is as follows

    # {"title": "Extracted content title in Chinese", "summary": "Extracted content subject, content not more than 300 words in Chinese", "translation": "Translated content of the article"}
    # 加载 llm 模型
    llm = ChatOpenAI(model_name="gpt-3.5-turbo-16k-0613")

    llm_chain = LLMChain(llm=llm, prompt=chat_prompt)

    print(datetime.now())
    input_list = [{"text": t} for t in split_chunks]
    result = llm_chain.apply(input_list)
    print(datetime.now())

    # result = llm_chain.generate(input_list)
    print(result)
    # print(result[0]["text"])

    ret = ""
    for r in result:
        ret += r.get("text")

    return ret


def test3():
    import requests

    API_URL = "http://147.182.254.122:3000/api/v1/prediction/a926552f-abc7-47b3-993c-b7dfa98d45d9"

    def query(payload):
        response = requests.post(API_URL, json=payload)
        return response.json()

    output = query(
        {
            "question": "Hey, how are you?",
        }
    )

    return output


import os

if __name__ == "__main__":
    os.environ["OPENAI_API_KEY"] = settings.OPENAI_KEY
    langchain_test2(text)
    # result = test3()
    # print(result)
