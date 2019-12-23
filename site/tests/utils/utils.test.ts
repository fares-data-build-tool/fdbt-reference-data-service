import {getHost} from "../../utils";

var MockReq = require('mock-req');

describe("utils", () => {
    describe("getHost", () => {
        it("should return http when host is localhost", () => {
            const expected = "http://localhost";
            const req = new MockReq({
                headers: {
                    'host': 'localhost'
                }
            });
            const result = getHost(req);
            expect(result).toEqual(expected);
        });

        it("should return https when host not localhost", () => {
            const expected = "https://a.com"
            const req = new MockReq({
                headers: {
                    'host': 'a.com'
                }
            });
            const result = getHost(req);
            expect(result).toEqual(expected);
        });
    });
});
