// 模块2：输出处理模块
module module2(
    input wire clk,
    input wire rst_n,
    input wire [7:0] data_in,
    input wire valid_in,
    output reg [7:0] data_out,
    output reg valid_out
);

    reg [1:0] delay_counter;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            data_out <= 8'h00;
            valid_out <= 1'b0;
            delay_counter <= 2'b00;
        end else begin
            if (valid_in) begin
                // 延迟2个周期输出
                if (delay_counter == 2'b10) begin
                    data_out <= data_in;
                    valid_out <= 1'b1;
                    delay_counter <= 2'b00;
                end else begin
                    delay_counter <= delay_counter + 1'b1;
                    valid_out <= 1'b0;
                end
            end else begin
                valid_out <= 1'b0;
            end
        end
    end

endmodule