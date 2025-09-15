#操作步骤
- https://newdrugs.dxy.cn/pc/drug PC登陆
- 输入检索药物名称
- 获得检索结果页面
- 页面链接前增加r.jina.ai，转化为markdown格式
- 保存后进行后续chunk格式转化处理

# 搜索药物curl命令，关键词为“伊立替康”
‘’‘
curl 'https://newdrugs.dxy.cn/pc/search?keyword=%E4%BC%8A%E7%AB%8B%E6%9B%BF%E5%BA%B7' \
  -H 'accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7' \
  -H 'accept-language: zh-CN,zh;q=0.9' \
  -b 'dxy_da_cookie-id=919df0c76d700689f59f3d80f5915d7e1757894592593; perf_dv6Tr4n=1; _ga=GA1.2.1577088910.1757894622; _gid=GA1.2.621081947.1757894622; _ga_C1KRQPKH2N=GS2.2.s1757894622$o1$g0$t1757894622$j60$l0$h0; JUTE_BBS_DATA=e517499d646ebede6abee1dda7802087f074ea81fecd238e0ad796f186b8289054998ee5bd97e780ce71526f0187f127a87eb31d7c7c024a8575f79b62ca3e25ec506691ce7df3669046955572086c86; CLASS_CASTGC=a52b7fd11868d11003e9e0407d8e7330714bd5f5b8ee97e6213ad1d54e5f870b64b5f046c3f075e3670926583968f911fedbd4a3507052cb152762eb60c773a6ca7219b048b1f2ac22959bde29ad270f2255c9cd6c0fdd1ad43bbd09c5f61e27a238e442eb516b3e283c5188c4bd7a037c33ca787e0890ba019dcbc457568589905820e2dc0d1a31ae9f82c01ee8873746e2f29904e96d373a121a02c01cc2903ace1a3aea3e2d2008ebf4138d082f60dc45685d568525c799c16f33162bcb3c36b5ecf296ffde645d8cd19713cafa2db746218156f15e21b483e229aeb43eff563051c9615719bdd071e76f244a8cfd495da52e6768423e40048df8602e9763; PHP_COMMON_CASTGC=54c93afeb13344e8d2baa8ac010f56f703b6846a86c563b696aade754aa5d38d01c46804ed20430b67772e1b18388aa556133a5194ef42c039e08b654bf2f748386e37d64461d500da7255bc0ad35024ac29e692eea398f4fb92d50958823b8039c59b71e3f2f165d8a8927762ae47c12b676783e1bc8468466ce1eed76f0a13412b52e7892bd170181497bb8fbfa57917eaf9ef2f4eb8138a5279793456508ef2f70701aa161bd7fc999e6f8e310ea3cfe93887b0a0623da7d3128a7d6b84e8bbbb12beac80865f5c2a0e7ad0e8f286d03430a14f9435e37a6e355ec10e4057903a33be2a5f7767c1306030b0340f0c565cb085f73c9236cf6324cdbadb3ac2' \
  -H 'priority: u=0, i' \
  -H 'sec-ch-ua: "Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "macOS"' \
  -H 'sec-fetch-dest: document' \
  -H 'sec-fetch-mode: navigate' \
  -H 'sec-fetch-site: none' \
  -H 'sec-fetch-user: ?1' \
  -H 'upgrade-insecure-requests: 1' \
  -H 'user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36'
’‘’

response:
/Users/qinxiaoqiang/Downloads/丁香园pc助手说明书获取/搜索伊立替康response.md



# 示例：检索药物“伊立替康”说明书，点击“易安达（盐酸伊立替康脂质体注射液）”

'''查询代码'''
curl 'https://newdrugs.dxy.cn/pc/drug/yX_cNIfiMy3fFKWqn3iwJLQ?ky=%E4%BC%8A%E7%AB%8B%E6%9B%BF%E5%BA%B7' \
  -H 'accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7' \
  -H 'accept-language: zh-CN,zh;q=0.9' \
  -b 'dxy_da_cookie-id=919df0c76d700689f59f3d80f5915d7e1757894592593; perf_dv6Tr4n=1; _ga=GA1.2.1577088910.1757894622; _gid=GA1.2.621081947.1757894622; _ga_C1KRQPKH2N=GS2.2.s1757894622$o1$g0$t1757894622$j60$l0$h0; JUTE_BBS_DATA=e517499d646ebede6abee1dda7802087f074ea81fecd238e0ad796f186b8289054998ee5bd97e780ce71526f0187f127a87eb31d7c7c024a8575f79b62ca3e25ec506691ce7df3669046955572086c86; CLASS_CASTGC=a52b7fd11868d11003e9e0407d8e7330714bd5f5b8ee97e6213ad1d54e5f870b64b5f046c3f075e3670926583968f911fedbd4a3507052cb152762eb60c773a6ca7219b048b1f2ac22959bde29ad270f2255c9cd6c0fdd1ad43bbd09c5f61e27a238e442eb516b3e283c5188c4bd7a037c33ca787e0890ba019dcbc457568589905820e2dc0d1a31ae9f82c01ee8873746e2f29904e96d373a121a02c01cc2903ace1a3aea3e2d2008ebf4138d082f60dc45685d568525c799c16f33162bcb3c36b5ecf296ffde645d8cd19713cafa2db746218156f15e21b483e229aeb43eff563051c9615719bdd071e76f244a8cfd495da52e6768423e40048df8602e9763; PHP_COMMON_CASTGC=54c93afeb13344e8d2baa8ac010f56f703b6846a86c563b696aade754aa5d38d01c46804ed20430b67772e1b18388aa556133a5194ef42c039e08b654bf2f748386e37d64461d500da7255bc0ad35024ac29e692eea398f4fb92d50958823b8039c59b71e3f2f165d8a8927762ae47c12b676783e1bc8468466ce1eed76f0a13412b52e7892bd170181497bb8fbfa57917eaf9ef2f4eb8138a5279793456508ef2f70701aa161bd7fc999e6f8e310ea3cfe93887b0a0623da7d3128a7d6b84e8bbbb12beac80865f5c2a0e7ad0e8f286d03430a14f9435e37a6e355ec10e4057903a33be2a5f7767c1306030b0340f0c565cb085f73c9236cf6324cdbadb3ac2' \
  -H 'priority: u=0, i' \
  -H 'sec-ch-ua: "Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "macOS"' \
  -H 'sec-fetch-dest: document' \
  -H 'sec-fetch-mode: navigate' \
  -H 'sec-fetch-site: none' \
  -H 'sec-fetch-user: ?1' \
  -H 'upgrade-insecure-requests: 1' \
  -H 'user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36'

  ## response内容
  /Users/qinxiaoqiang/Downloads/丁香园pc助手说明书获取/点击搜索结果中易安达response.md


  # 爬虫开发要求
  - 模拟浏览器操作
  - 用户选择菜单，输入查询关键词后，获取查询结果
  - 用户选择查询结果中的药品，获取药品详情
  - 药品详情中包含药品名称、规格、生产企业、生产地址、生产日期、有效期、使用方法、注意事项、警告事项、其他信息
  - 提取返回的药物说明书内容，保持结构，保存为markdown格式文件。
  - 进行RAG embedding预处理：对于切分前的各种格式文档，进行预处理，从而提高chunk的准确且分。通过：
    1. 增加行号如<1>,<2>
    2. 增加chunk切分标记符号如"+","//"等
    3. 根据主题和内容进行分段，插入分段提示"======"，进行主题段落区分
    Rules: 不要修改文档内容，只进行格式整理，只允许修改chunk和符号，序号。输出前进行二次检查。处理文件添加后缀"_optimized"后，以markdown文件格式保存在同路径下。
  - 保存处理后的文件，提示处理完成。

  