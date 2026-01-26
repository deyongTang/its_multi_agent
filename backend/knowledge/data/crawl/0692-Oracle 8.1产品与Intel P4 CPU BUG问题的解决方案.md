# 知识库 692

## 标题
Oracle 8.1产品与Intel P4 CPU BUG问题的解决方案

## 问题描述
Oracle 8.1产品与Intel P4 CPU BUG问题的解决方案

## 分类
主类别: 预装软件
子类别: 其他随机软件

## 关键词
服务器, 万全, 手册, Oracle 8.1, Intel P4, CPU

## 元信息
创建时间:2024-12-15|版本:1.0

## 解决方案
Oracle 8.1的产品对P4 的[CPU](/detail/kd_17345.html)有一个[BUG](/detail/kd_17831.html)。ORACLE 提出解决办法如下：

1、Create a temporary directory on your server（在你的[服务器](/detail/kd_17589.html)上创建一个临时目录）

2、Copy the contents of the Oracel 8i Server CD to the temporary directory created in step1.（把ORACLE 8i Server CD 的内容拷贝到刚创建的临时目录中）

3、Search the directory structure created in step 1 for the existence of the filename symcjit.dll（在刚才建立的目录中查找文件symcjit.dll）

4、Rename each copy of the symcjit.dll to symcjit.old（更改每一个symcjit.dll的拷贝的名称为symcjit.old）

5、Run the [setup.exe](/detail/kd_17507.html) f[rom](/detail/kd_17708.html) the \\install\\win32 directory and install Oracle 8.1.x.（从\\install\\win32目录下运行Setup.exe并安装Oracle 8.1.x。

总结：将安装盘中的所有文件复制到本地,找到文件 symcjit.dll ,将它改为 symcjit.old;然后运行安装。

<!-- 文档主题：Oracle 8.1产品与Intel P4 CPU BUG问题的解决方案 (知识库库编号: 692) -->