// Simple test module
module top (
    input wire clk,
    input wire rst,
    output reg [7:0] led
);
    reg [31:0] counter;

    always @(posedge clk) begin
        if (rst) begin
            counter <= 32'h0;
            led <= 8'h00;
        end else begin
            counter <= counter + 1;
            if (counter == 32'd10000000) begin
                led <= led + 1;
                counter <= 32'h0;
            end
        end
    end
endmodule