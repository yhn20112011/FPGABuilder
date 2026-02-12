// my_zynq_project 顶层模块
// 由FPGABuilder自动生成

module my_zynq_project_top (
    input wire clk,
    input wire rst_n,
    input wire  data_in,
    output wire data_out,
    output wire valid_out
);

    // 示例：简单的流水线寄存器
    reg [7:0] data_reg;
    reg valid_reg;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            data_reg <= 8'h0;
            valid_reg <= 1'b0;
        end else begin
            data_reg <= data_in;
            valid_reg <= 1'b1;
        end
    end

    assign data_out = data_reg;
    assign valid_out = valid_reg;

endmodule
