// 顶层模块
module top(
    input wire clk,
    input wire rst_n,
    input wire [7:0] data_in,
    output wire [7:0] data_out,
    output wire valid_out
);

    // 内部信号
    wire [7:0] module1_out;
    wire module1_valid;

    // 实例化module1
    module1 u_module1(
        .clk(clk),
        .rst_n(rst_n),
        .data_in(data_in),
        .data_out(module1_out),
        .valid_out(module1_valid)
    );

    // 实例化module2
    module2 u_module2(
        .clk(clk),
        .rst_n(rst_n),
        .data_in(module1_out),
        .valid_in(module1_valid),
        .data_out(data_out),
        .valid_out(valid_out)
    );

endmodule