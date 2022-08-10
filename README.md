<div align="center">
    <img width="200" src="starving_logo.gif" alt="logo">

# What to Eat/Drink

<!-- prettier-ignore-start -->
<!-- markdownlint-disable-next-line MD036 -->
_🧃🧋🍔🌮🍜🍮🍣🍻🍩 今天吃/喝什么 🍩🍻🍣🍮🍜🌮🍔🧋🧃_
<!-- prettier-ignore-end -->

</div>

<p align="center">
  
  <a href="https://github.com/MinatoAquaCrews/nonebot_plugin_what2eat/blob/beta/LICENSE">
    <img src="https://img.shields.io/github/license/MinatoAquaCrews/nonebot_plugin_what2eat?color=blue">
  </a>
  
  <a href="https://github.com/nonebot/nonebot2">
    <img src="https://img.shields.io/badge/nonebot2-2.0.0b3+-green">
  </a>
  
  <a href="https://github.com/MinatoAquaCrews/nonebot_plugin_what2eat/releases/tag/v0.3.4a2">
    <img src="https://img.shields.io/github/v/release/MinatoAquaCrews/nonebot_plugin_what2eat?color=orange&include_prereleases">
  </a>

  <a href="https://www.codefactor.io/repository/github/MinatoAquaCrews/nonebot_plugin_what2eat">
    <img src="https://img.shields.io/codefactor/grade/github/MinatoAquaCrews/nonebot_plugin_what2eat/beta?color=red">
  </a>
  
</p>

## 版本

v0.3.4a2 今天喝什么！菜品可以添加配图啦！

⚠ 适配nonebot2-2.0.0b3+

[更新日志](https://github.com/MinatoAquaCrews/nonebot_plugin_what2eat/releases/tag/v0.3.4a2)

## 安装

1. 通过`pip`或`nb`安装；

2. 数据默认位于`./resource`下`eating.json`、`drinks.json`与`greetings.json`，菜品的附图储存于`./resource/img`下。可通过设置`env`下`WHAT2EAT_PATH`更改；

    ```python
    WHAT2EAT_PATH="your-path-to-resource"
    ```

## 功能

1. 🔥 **新增** 选择恐惧症？让Bot建议你今天吃/喝什么！

    👉 新增一点点、茶颜悦色、蜜雪冰城、茶百道、瑞幸咖啡、CoCo都可！预置菜单加入了更多菜品！

2. **插件配置**

    ``` python
    WHAT2EAT_PATH="your-path-to-resource"			# 资源路径
    USE_PRESET_MENU=false							# 是否从repo中下载预置基础菜单，默认为False，请注意会覆盖原有的文件！
    USE_PRESET_GREETINGS=false                    	# 是否从repo中下载预置问候语，默认为False
    EATING_LIMIT=5									# 每个时段吃/喝什么次数上限，默认5次；每日6点、11点、17点、22点自动刷新
    GREETING_GROUPS_ID=["123456789", "987654321"]	# 默认开启小助手群组，或{"123456789", "987654321"}
    SUPERUSERS={"12345678"}							# 同nonebot超管配置
    ```

3. 群管理可自行添加或移除群特色菜单（位于`eating.json`下`[group_food][group_id]`）；超管可添加或移除基础菜单（`[basic_food]`）；

    - 菜品文字与配图一一对应才视为相同的菜品，例如：文字相同而配图不同、文字与文字+配图、或文字不同而配图相同，这几种均视为不同菜品

    - 当移除的菜品包含配图时，会一并移除相同配图的其他菜品

4. 各群特色菜单相互独立；各群每个时间段询问Bot建议次数独立；Bot会综合各群菜单+基础菜单给出建议；

5. 吃饭小助手：每天7、12、15、18、22点群发问候语提醒群友吃饭/摸鱼/下班，`GREETING_GROUPS_ID`设置常开的群号列表（或集合），每次启动插件时将置`True`，形如：

    ```python
    GREETING_GROUPS_ID=["123456789", "987654321"]	# 名字长防止与其他插件配置名相同
    ```

    ⚠ 群吃饭小助手启用配置存于`greetings.json`的`groups_id`字段

6. 初次使用该插件时，若不存在`eating.json`与`greetings.json`文件，设置`USE_PRESET_MENU`及`USE_PRESET_GREETINGS`可从仓库中尝试下载；会尝试从仓库中下载`drinks.json`。若资源下载失败且本地也不存在，则抛出错误。

    ```python
    USE_PRESET_MENU=false
    USE_PRESET_GREETINGS=false
    ```

    ⚠ 从仓库下载会**覆写**原有文件！建议用户按需开启此配置

## 命令

1. 吃什么：今天吃什么、中午吃啥、今晚吃啥、中午吃什么、晚上吃啥、晚上吃什么、夜宵吃啥……

2. 🔥 **新增** 喝什么： 今天喝什么、中午喝啥、今晚喝啥、中午喝什么、晚上喝啥、晚上喝什么、夜宵喝啥……

    ⚠ 与吃什么共用`EATING_LIMIT`次数

3. [管理员或超管] 添加或移除群菜名：[添加/移除 菜名]；

    💥 添加菜品与加菜可以附配图啦！

4. 查看群菜单：[菜单/群菜单/查看菜单]；

5. [超管] 添加至基础菜单：[加菜 菜名]；

6. 查看基础菜单：[基础菜单]；

7. [管理员或超管] 开启/关闭吃饭小助手：[开启/启用/关闭/禁用小助手]；

8. [管理员或超管] 添加/删除吃饭小助手问候语：[添加/删除/移除问候 时段 问候语]；

    ⚠ 添加/移除问候操作可一步步进行，或一次性输入两或三个命令；可中途取消操作

## 效果

1. 示例1

    Q：今晚吃什么

    A：建议肯德基

    Q：今晚喝啥

    A：不如来杯 茶颜悦色 的 幽兰拿铁 吧！

    Q：今晚吃什么

    A：你今天已经吃得够多了！

    Q：群菜单

    A：

    ---群特色菜单---

    alpha

    beta

    gamma

2. 示例2

    [群管] Q：添加 派蒙

    A：派蒙 已加入群特色菜单~

    [超管] Q：加菜 东方馅挂炒饭

    A：东方馅挂炒饭 已加入基础菜单~

    [群管] Q：移除 东方馅挂炒饭

    A：东方馅挂炒饭 在基础菜单中，非超管不可操作哦~

3. 示例3

    [群管] Q：添加问候

    A：请输入添加问候语的时段，可选：早餐/午餐/摸鱼/晚餐/夜宵，输入取消以取消操作

    [群管] Q：摸鱼

    A：请输入添加的问候语，输入取消以取消操作

    [群管] Q：你好

    A：你好 已加入 摸鱼问候~

## 本插件改自

[HoshinoBot-whattoeat](https://github.com/pcrbot/whattoeat)

部分菜名参考[程序员做饭指南](https://github.com/Anduin2017/HowToCook)