<div align="center">

# What to Eat

<!-- prettier-ignore-start -->
<!-- markdownlint-disable-next-line MD036 -->
_🍔 今天吃什么 🍔_
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
    <img src="https://img.shields.io/badge/release-v0.1.0-orange">
  </a>
  
</p>

</p>

## 版本

v0.1.0

⚠ 适配nonebot2-2.0.0alpha.16！

## 安装

1. 通过`pip`或`poetry`安装；

2. 菜单及群友吃什么的数据默认位于`./resource/data.json`，可通过设置`env`下`WHAT2EAT_PATH`更改；群友询问Bot的次数会记录在该文件中；

## 功能

1. 选择恐惧症？让Bot给三餐你吃什么建议；

2. 每餐Bot提出建议上限可通过`EATING_LIMIT`修改（默认5次），每日6点、11点、17点自动刷新次数；

3. 群友可自行添加或移除菜品，或许需要加权限限制🤔；

## 命令

1. 吃什么：今天吃什么、中午吃啥、今晚吃啥、中午吃什么、晚上吃啥、晚上吃什么……

2. 添加或移除：添加/移除 菜名；

## 本插件改自：

[HoshinoBot-whattoeat](https://github.com/pcrbot/whattoeat)