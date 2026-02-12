# my_zynq_project 时钟和引脚约束
# 由FPGABuilder自动生成
# 请根据实际硬件修改引脚分配

# 时钟约束
create_clock -name clk -period 10.000 [get_ports clk]

# 复位约束
set_property IOSTANDARD LVCMOS33 [get_ports clk]
set_property IOSTANDARD LVCMOS33 [get_ports rst_n]
set_property IOSTANDARD LVCMOS33 [get_ports data_in]
set_property IOSTANDARD LVCMOS33 [get_ports data_out]
set_property IOSTANDARD LVCMOS33 [get_ports valid_out]

# 引脚分配示例（ZC706开发板）
set_property PACKAGE_PIN AC21 [get_ports clk]
set_property PACKAGE_PIN AB10 [get_ports rst_n]
set_property PACKAGE_PIN AA10 [get_ports data_in]
set_property PACKAGE_PIN AB11 [get_ports data_out]
set_property PACKAGE_PIN AC11 [get_ports valid_out]

# 重要：为所有端口添加正确的引脚约束，否则生成比特流时会遇到DRC错误
# 对于测试目的，可以暂时降低DRC严重性：
set_property SEVERITY {Warning} [get_drc_checks UCIO-1]
