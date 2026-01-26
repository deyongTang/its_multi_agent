# 知识库 243

## 标题
Windows 8系统使用文件历史记录备份、恢复数据

## 问题描述
Windows 8系统使用文件历史记录备份、恢复数据方法的指导。

## 分类
主类别: 操作系统故障
子类别: 系统数据恢复

## 关键词
查看, 设置, 管理, Windows, 历史纪录备份, 恢复数据

## 元信息
创建时间:2024-12-15|版本:2.0

## 解决方案
在Windows 8中，文件历史记录会自动备份位于库、联系人、收藏夹、Microsoft SkyDrive 中以及桌面上的文件。但是备份的目标必须是外部存储设备，如：U盘、移动硬盘、网络位置。备份的文件将以时间为顺序，不断生成备份文件，可以方便找回某个时间段的某一个数据或者多个数据。

1、按“**Windows徽标键+I键**”---“**控制面板**”---“**系统与安全**”---“**文件历史记录**”；

![](http://robotrs.lenovo.com.cn/ZmptY2NtYW5hZ2Vy/p4data/Rdata/Rfiles/126.files/image001.jpg)

2、文件历史记录功能默认是关闭的，点击[启动](/detail/kd_17514.html)就可以开启，第一次使用需要选择[驱动](/detail/kd_17488.html)器，可以选择外部驱动器（[移动硬盘](/detail/kd_17404.html)或者U盘）和网络位置，网络位置需要建立[家庭组](/detail/kd_17699.html)，然后将文件备份到家庭组的其他成员电脑硬盘上，由于笔者没有建立家庭组，这里只展示使用U盘的相关功能，网络的使用也大同小异。（注：如果既无外部存储设备，也无网络环境，将无法启用此功能）

![](http://robotrs.lenovo.com.cn/ZmptY2NtYW5hZ2Vy/p4data/Rdata/Rfiles/126.files/image002.jpg)

3、文件历史记录并不支持主动选取驱动器文件夹，只支持链接到库，但其实一样，我们可以将需要备份的文件关联到库，默认是备份所有库里面的文件，如果我们不需要备份大量无用的[高清](/detail/kd_17423.html)[视频](/detail/kd_17880.html)或者音乐文件，可以在排除文件夹中选择不需要的库文件，这里去掉了大量不重要的视频文件；

![](http://robotrs.lenovo.com.cn/ZmptY2NtYW5hZ2Vy/p4data/Rdata/Rfiles/126.files/image003.jpg)

4、点击立即运行，即可备份库文件，速度取决于你的库内文件的大小，第一次速度较慢，现在显示文件历史记录正在备份你的文件副本，这时候移除U盘，将会破坏你的备份数据，耐心等待一段时间，就会备份完毕。

![](http://robotrs.lenovo.com.cn/ZmptY2NtYW5hZ2Vy/p4data/Rdata/Rfiles/126.files/image004.jpg)

5、这时候我们打开U盘，就会看到如下文件夹。其中Configuration里面xml文件，就是对备份数据的布局管理，这一部分我们不需要了解，我们备份 的数据都保存在Date文件夹中，我们可以在里面读取文件，但是这样闲的很麻烦，我们可以在文件历史记录中通过还原个人文件来找回备份的数据。

![](http://robotrs.lenovo.com.cn/ZmptY2NtYW5hZ2Vy/p4data/Rdata/Rfiles/126.files/image006.jpg)

6、点击左边栏的还原个人文件，就会看到一个可以左右选择的界面，我们对库里面的文件进行每一次更改，系统就会自动按照默认的时间频率更新里面的数据，4/4 就表示我对文件进行了4次的更改，每一次的数据都保存了下来，如果我们想要恢复其中任何一次的数据，点击绿色按钮就会恢复当时的文件。

![](http://robotrs.lenovo.com.cn/ZmptY2NtYW5hZ2Vy/p4data/Rdata/Rfiles/126.files/image008.jpg)

![](http://robotrs.lenovo.com.cn/ZmptY2NtYW5hZ2Vy/p4data/Rdata/Rfiles/126.files/image009.jpg)

7、这里选择一个时间段，就可以恢复数据。

![](http://robotrs.lenovo.com.cn/ZmptY2NtYW5hZ2Vy/p4data/Rdata/Rfiles/126.files/image011.jpg)

8、如果数据中的大量文件没有进行更改，系统就会跳过这一部分，原本以为需要大量时间完成恢复，跳过了这些项目，很快就完成了。

![](http://robotrs.lenovo.com.cn/ZmptY2NtYW5hZ2Vy/p4data/Rdata/Rfiles/126.files/image013.jpg)

9、在高级设置里面可以更改系统保存文件的频率，默认是一小时，当然如果我们需要现在更新，也可以手动更新。也可以更改脱机[缓存](/detail/kd_17389.html)的大小，保存的版本，选择默认的设置即可。

![](http://robotrs.lenovo.com.cn/ZmptY2NtYW5hZ2Vy/p4data/Rdata/Rfiles/126.files/image015.jpg)

<!-- 文档主题：Windows 8系统使用文件历史记录备份、恢复数据 (知识库库编号: 243) -->