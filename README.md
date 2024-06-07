# plugin.video.duolasousuo

哆啦搜索（Kodi视频插件）

> 声明：本插件是基于学习和研究目的通过爬虫技术所抓取的所有内容均来自于第三方网站的数据，插件不涉及资源存储或分发。作者不对其内容承担任何责任！仅供个人学习交流之用，24小时内请自觉卸载，勿作商业用途。


### 如何下载

插件可以從 releases 選項下載。 請勿嘗試安裝GitHub自動生成的 .zip


### 如何更換其他資源站數據接口？

插件在設置面板中提供了一個設定項目，您可以在修改【內置搜索引擎接口】為你所需要的資源站數據接口，那麽程序就會按照該預設的地址去獲取資源。


### 如何啟用雲端引擎接口？

爲了方便测试练习，插件默認的雲端引擎并沒有開啓，開啓后它將支持獲取基於github上搜索引擎接口列表，使插件擁有更多的搜索渠道。

>  云端引擎的接口数据格式如下（即：代碼中[ADDON_api]變量對應返回的内容）：

```json

{
  "code": 1, // API状态：1为可用
  "message": "success", // API状态描述
  "expires_in": 3600, // API有效期：单位为秒
  "readme": "hello", // API简介：[1.7]版本起开始弃用!
  "notice": "5qyi6L+O5YWJ5Li05Li76aG177yaaHR0cHM6Ly9tYWxpbWFsaWFvLmdpdGh1Yi5pby9rb2RpLw==", // API通知消息：要求内容采用base64编码
  "client": "1.7.0", // 版本号
  "data": {
    "time": "2024-06-07 17:09:02", // 数据更新时间
    "note": "", // 数据更新备注
    "list": [ // 数据源列表
      {
        "name": "1.飞速资源", // 数据源名称
        "status": 1, // 数据源状态：1为可用
        "api_url": "aHR0cHM6Ly93d3cuZmVpc3V6eWFwaS5jb20vYXBpLnBocC9wcm92aWRlL3ZvZC8=" // 数据源接口地址：要求内容采用base64编码
      },
      {
        "name": "2.无极网络", // 数据源名称
        "status": 1, // 数据源状态：1为可用
        "api_url": "aHR0cHM6Ly9hcGkud3VqaW5hcGkubWUvYXBpLnBocC9wcm92aWRlL3ZvZC8=" // 数据源接口地址：要求内容采用base64编码
      }
    ]
  }
}

```


### 什麽是資源站數據接口？

> 當前程序是完全基於目前互聯網第三方的資源站的Json數據接口進行獲取内容並構造到kodi中的，那麽什麽是接口呢，又如何尋找它？

請您Google下面这些关键词，并寻找这些第三方站点中的json api接口。資源站json接口通常非常类似，
例如我们找到了他们的json接口是这样举例的：https://api.123.com/api.php/provide/vod/?ac=list
那么其实它的接口就是：<u>https://api.123.com/api.php/provide/vod/</u>

其中问好后面的都是参数，例如?ac=list是一个参数。

```

資源站、采集站、资源帮助中心、
/api.php/provide/vod/
/cjapi/mc10/vod/json.html
/inc/api_mac10.php

```

通過搜索以上關鍵詞，應該可以找到他們。
