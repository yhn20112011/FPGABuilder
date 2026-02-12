// 模块1：数据处理模块
module module1(
    input wire clk,
    input wire rst_n,
    input wire [7:0] data_in,
    output reg [7:0] data_out,
    output reg valid_out
);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            data_out <= 8'h00;
            valid_out <= 1'b0;
        end else begin
            // 简单处理：数据加1
            data_out <= data_in + 8'h01;
            valid_out <= 1'b1;
        end
    end

endmodule