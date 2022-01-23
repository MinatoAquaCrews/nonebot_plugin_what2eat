<div align="center">

# What to Eat

<!-- prettier-ignore-start -->
<!-- markdownlint-disable-next-line MD036 -->
_🍔🌮🍜🍮🍣 今天吃什么 🍣🍮🍜🌮🍔_
<!-- prettier-ignore-end -->

</div>

<p align="center">
  
  <a href="https://github.com/KafCoppelia/nonebot_plugin_what2eat/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/license-MIT-informational">
  </a>
  
  <a href="https://github.com/nonebot/nonebot2">
    <img src="https://img.shields.io/badge/nonebot2-2.0.0alpha.16-green">
  </a>
  
  <a href="">
    <img src="https://img.shields.io/badge/release-v0.1.1-orange">
  </a>
  
</p>

</p>

## 版本

v0.1.1

⚠ 适配nonebot2-2.0.0alpha.16，适配beta.1版本将会放在dev分支。

## 安装

1. 通过`pip`或`nb`安装；

2. 数据默认位于`./resource/data.json`，可通过设置`env`下`WHAT2EAT_PATH`更改；基础菜单、群特色菜单及群友询问Bot次数会记录在该文件中；

## 功能

1. 选择恐惧症？让Bot给你今天吃什么建议！🍱

2. 每餐每个时间段询问Bot建议上限可通过`EATING_LIMIT`修改（默认6次），每日6点、11点、17点、22点（夜宵）自动刷新；

3. 群管理可自行添加或移除群特色菜单（`data.json`下`[group_food][group_id]`）；超管可添加或移除基础菜单（`[basic_food]`）；

4. 各群特色菜单相互独立；各群每个时间段询问Bot建议次数独立；Bot会**综合各群特色菜单及基础菜单**给出建议；

5. *TODO*：提醒按时吃饭小助手🤔，在做了在做了……

## 命令

1. 吃什么：今天吃什么、中午吃啥、今晚吃啥、中午吃什么、晚上吃啥、晚上吃什么、夜宵吃啥……

2. [管理或群主或超管权限] 添加或移除：添加/移除 菜名；

3. 查看菜单：查看菜单/群菜单；

4. [仅超管权限] 加菜至基础菜单：加菜 菜名；

## 注意

尽量避免**基础菜单为空**情况，已在`./resource/data.json`内`[basic_food]`中写入几项。

## 本插件改自：

[HoshinoBot-whattoeat](https://github.com/pcrbot/whattoeat)