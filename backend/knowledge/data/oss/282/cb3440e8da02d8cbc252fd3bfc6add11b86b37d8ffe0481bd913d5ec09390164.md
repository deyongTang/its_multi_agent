# 知识库 282

## 标题
如何在Windows系统中对分区进行压缩

## 问题描述
Windows系统中可以对某个分区进行压缩，通过压缩该分区的容量，来缩小该分区容量。压缩出来的容量将显示为空闲容量，可以再次划分为一个分区。具体可以压缩多少容量由系统本身来测算。如何操作呢？一起来看下本文……

## 分类
主类别: 操作系统故障
子类别: 磁盘分区

## 关键词
分区, 分区压缩, 设置, 管理, Windows, 压缩券, 压缩

## 元信息
创建时间:2024-12-15|版本:1.0

## 解决方案
Windows系统中可以对某个分区进行压缩，通过压缩该分区的容量，来缩小该分区容量。压缩出来的容量将显示为空闲容量，可以再次划分为一个分区。具体可以压缩多少容量由系统本身来测算。

[Windows 7](/detail/kd_17984.html)、[Windows 8](/detail/kd_17985.html)操作系统（Windows XP无此功能）

1、按“**Windows[徽标键](/detail/kd_17845.html)+R键**”，输入“**diskmgmt.msc**”点击“**确定**”；

![](http://robotrs.lenovo.com.cn/ZmptY2NtYW5hZ2Vy/p4data/Rdata/Rfiles/121.files/image001.jpg)

2、打开“**[磁盘](/detail/kd_17452.html)管理**”主界面，选中需要压缩的分区，如D盘，鼠标右击选择“**[压缩卷](/detail/kd_17492.html)**”；

![](http://robotrs.lenovo.com.cn/ZmptY2NtYW5hZ2Vy/p4data/Rdata/Rfiles/121.files/image002.jpg)

3、在“**输入压缩空间量**”，输入需要压缩的容量，单位MB。上面有可以压缩的最大容量，这是系统计算出来的，所以输入的数字不能大于最大值。输入完毕后点击“压缩”，即可开始压缩过程，过程长短依据数据量不同。（此处整个分区都是空的，所以最大压缩值比较大）

![](http://robotrs.lenovo.com.cn/ZmptY2NtYW5hZ2Vy/p4data/Rdata/Rfiles/121.files/image003.jpg)

4、压缩完毕后可以看到，原来20G的分区，被压缩成[3G](/detail/kd_17620.html)的分区，压缩出来的容量变为未分配空间，可以再次建立分区。

![](http://robotrs.lenovo.com.cn/ZmptY2NtYW5hZ2Vy/p4data/Rdata/Rfiles/121.files/image004.jpg)

<!-- 文档主题：如何在Windows系统中对分区进行压缩 (知识库库编号: 282) -->