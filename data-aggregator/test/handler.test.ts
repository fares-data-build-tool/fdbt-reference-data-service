import * as Handler from "../handler";
import { Callback, Context } from "aws-lambda";
import MockContext from "aws-lambda-mock-context";

describe("aws handler", () => {
  it("should call console.log", () => {
    const event = {
      Name: "Danny"
    };
    const context: Context = MockContext();
    const callback: Callback = jest.fn();

    const globalAny: any = global;
    globalAny.console = {
      log: jest.fn()
    };

    Handler.s3hook(event, context, callback);
    expect(globalAny.console.log).toHaveBeenCalledWith(JSON.stringify(event));
  });

  it("should stringify the event", () => {
    const event = {
      Number: 54
    };
    const context: Context = MockContext();
    const callback: Callback = jest.fn();
     
    const stringifySpy = jest.spyOn(JSON, 'stringify');

    Handler.s3hook(event, context, callback);
    expect(stringifySpy).toHaveBeenCalledWith(event);
  });
});
