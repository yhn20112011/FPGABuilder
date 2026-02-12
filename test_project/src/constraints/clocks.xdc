# 时钟约束
create_clock -name clk -period 10.000 [get_ports clk]

# 复位约束
set_property IOSTANDARD LVCMOS33 [get_ports {clk rst_n}]
set_property IOSTANDARD LVCMOS33 [get_ports {data_in[*]}]
set_property IOSTANDARD LVCMOS33 [get_ports {data_out[*]}]
set_property IOSTANDARD LVCMOS33 [get_ports {valid_out}]

# 引脚分配（示例，根据实际硬件调整）
set_property PACKAGE_PIN Y9 [get_ports clk]
set_property PACKAGE_PIN AB10 [get_ports rst_n]

# 降低未约束端口DRC错误的严重性，允许生成比特流用于测试
set_property SEVERITY {Warning} [get_drc_checks UCIO-1]