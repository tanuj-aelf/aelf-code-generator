"use strict";
/*
 * ATTENTION: An "eval-source-map" devtool has been used.
 * This devtool is neither made for production nor for readable output files.
 * It uses "eval()" calls to create a separate source file with attached SourceMaps in the browser devtools.
 * If you are trying to read the output file, select a different devtool (https://webpack.js.org/configuration/devtool/)
 * or disable the default devtool with "devtool: false".
 * If you are looking for production-ready output files, see mode: "production" (https://webpack.js.org/configuration/mode/).
 */
exports.id = "vendor-chunks/untruncate-json";
exports.ids = ["vendor-chunks/untruncate-json"];
exports.modules = {

/***/ "(ssr)/./node_modules/untruncate-json/dist/esm/index.js":
/*!********************************************************!*\
  !*** ./node_modules/untruncate-json/dist/esm/index.js ***!
  \********************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

eval("__webpack_require__.r(__webpack_exports__);\n/* harmony export */ __webpack_require__.d(__webpack_exports__, {\n/* harmony export */   \"default\": () => (/* binding */ untruncateJson)\n/* harmony export */ });\nfunction isWhitespace(char) {\n    return \"\\u0020\\u000D\\u000A\\u0009\".indexOf(char) >= 0;\n}\nfunction untruncateJson(json) {\n    var contextStack = [\"topLevel\" /* TOP_LEVEL */];\n    var position = 0;\n    var respawnPosition;\n    var respawnStackLength;\n    var respawnReason;\n    var push = function (context) { return contextStack.push(context); };\n    var replace = function (context) {\n        return (contextStack[contextStack.length - 1] = context);\n    };\n    var setRespawn = function (reason) {\n        if (respawnPosition == null) {\n            respawnPosition = position;\n            respawnStackLength = contextStack.length;\n            respawnReason = reason;\n        }\n    };\n    var clearRespawn = function (reason) {\n        if (reason === respawnReason) {\n            respawnPosition = undefined;\n            respawnStackLength = undefined;\n            respawnReason = undefined;\n        }\n    };\n    var pop = function () { return contextStack.pop(); };\n    var dontConsumeCharacter = function () { return position--; };\n    var startAny = function (char) {\n        if (\"0\" <= char && char <= \"9\") {\n            push(\"number\" /* NUMBER */);\n            return;\n        }\n        switch (char) {\n            case '\"':\n                push(\"string\" /* STRING */);\n                return;\n            case \"-\":\n                push(\"numberNeedsDigit\" /* NUMBER_NEEDS_DIGIT */);\n                return;\n            case \"t\":\n                push(\"true\" /* TRUE */);\n                return;\n            case \"f\":\n                push(\"false\" /* FALSE */);\n                return;\n            case \"n\":\n                push(\"null\" /* NULL */);\n                return;\n            case \"[\":\n                push(\"arrayNeedsValue\" /* ARRAY_NEEDS_VALUE */);\n                return;\n            case \"{\":\n                push(\"objectNeedsKey\" /* OBJECT_NEEDS_KEY */);\n                return;\n        }\n    };\n    for (var length = json.length; position < length; position++) {\n        var char = json[position];\n        switch (contextStack[contextStack.length - 1]) {\n            case \"topLevel\" /* TOP_LEVEL */:\n                startAny(char);\n                break;\n            case \"string\" /* STRING */:\n                switch (char) {\n                    case '\"':\n                        pop();\n                        break;\n                    case \"\\\\\":\n                        setRespawn(\"stringEscape\" /* STRING_ESCAPE */);\n                        push(\"stringEscaped\" /* STRING_ESCAPED */);\n                        break;\n                }\n                break;\n            case \"stringEscaped\" /* STRING_ESCAPED */:\n                if (char === \"u\") {\n                    push(\"stringUnicode\" /* STRING_UNICODE */);\n                }\n                else {\n                    clearRespawn(\"stringEscape\" /* STRING_ESCAPE */);\n                    pop();\n                }\n                break;\n            case \"stringUnicode\" /* STRING_UNICODE */:\n                if (position - json.lastIndexOf(\"u\", position) === 4) {\n                    clearRespawn(\"stringEscape\" /* STRING_ESCAPE */);\n                    pop();\n                }\n                break;\n            case \"number\" /* NUMBER */:\n                if (char === \".\") {\n                    replace(\"numberNeedsDigit\" /* NUMBER_NEEDS_DIGIT */);\n                }\n                else if (char === \"e\" || char === \"E\") {\n                    replace(\"numberNeedsExponent\" /* NUMBER_NEEDS_EXPONENT */);\n                }\n                else if (char < \"0\" || char > \"9\") {\n                    dontConsumeCharacter();\n                    pop();\n                }\n                break;\n            case \"numberNeedsDigit\" /* NUMBER_NEEDS_DIGIT */:\n                replace(\"number\" /* NUMBER */);\n                break;\n            case \"numberNeedsExponent\" /* NUMBER_NEEDS_EXPONENT */:\n                if (char === \"+\" || char === \"-\") {\n                    replace(\"numberNeedsDigit\" /* NUMBER_NEEDS_DIGIT */);\n                }\n                else {\n                    replace(\"number\" /* NUMBER */);\n                }\n                break;\n            case \"true\" /* TRUE */:\n            case \"false\" /* FALSE */:\n            case \"null\" /* NULL */:\n                if (char < \"a\" || char > \"z\") {\n                    dontConsumeCharacter();\n                    pop();\n                }\n                break;\n            case \"arrayNeedsValue\" /* ARRAY_NEEDS_VALUE */:\n                if (char === \"]\") {\n                    pop();\n                }\n                else if (!isWhitespace(char)) {\n                    clearRespawn(\"collectionItem\" /* COLLECTION_ITEM */);\n                    replace(\"arrayNeedsComma\" /* ARRAY_NEEDS_COMMA */);\n                    startAny(char);\n                }\n                break;\n            case \"arrayNeedsComma\" /* ARRAY_NEEDS_COMMA */:\n                if (char === \"]\") {\n                    pop();\n                }\n                else if (char === \",\") {\n                    setRespawn(\"collectionItem\" /* COLLECTION_ITEM */);\n                    replace(\"arrayNeedsValue\" /* ARRAY_NEEDS_VALUE */);\n                }\n                break;\n            case \"objectNeedsKey\" /* OBJECT_NEEDS_KEY */:\n                if (char === \"}\") {\n                    pop();\n                }\n                else if (char === '\"') {\n                    setRespawn(\"collectionItem\" /* COLLECTION_ITEM */);\n                    replace(\"objectNeedsColon\" /* OBJECT_NEEDS_COLON */);\n                    push(\"string\" /* STRING */);\n                }\n                break;\n            case \"objectNeedsColon\" /* OBJECT_NEEDS_COLON */:\n                if (char === \":\") {\n                    replace(\"objectNeedsValue\" /* OBJECT_NEEDS_VALUE */);\n                }\n                break;\n            case \"objectNeedsValue\" /* OBJECT_NEEDS_VALUE */:\n                if (!isWhitespace(char)) {\n                    clearRespawn(\"collectionItem\" /* COLLECTION_ITEM */);\n                    replace(\"objectNeedsComma\" /* OBJECT_NEEDS_COMMA */);\n                    startAny(char);\n                }\n                break;\n            case \"objectNeedsComma\" /* OBJECT_NEEDS_COMMA */:\n                if (char === \"}\") {\n                    pop();\n                }\n                else if (char === \",\") {\n                    setRespawn(\"collectionItem\" /* COLLECTION_ITEM */);\n                    replace(\"objectNeedsKey\" /* OBJECT_NEEDS_KEY */);\n                }\n                break;\n        }\n    }\n    if (respawnStackLength != null) {\n        contextStack.length = respawnStackLength;\n    }\n    var result = [\n        respawnPosition != null ? json.slice(0, respawnPosition) : json,\n    ];\n    var finishWord = function (word) {\n        return result.push(word.slice(json.length - json.lastIndexOf(word[0])));\n    };\n    for (var i = contextStack.length - 1; i >= 0; i--) {\n        switch (contextStack[i]) {\n            case \"string\" /* STRING */:\n                result.push('\"');\n                break;\n            case \"numberNeedsDigit\" /* NUMBER_NEEDS_DIGIT */:\n            case \"numberNeedsExponent\" /* NUMBER_NEEDS_EXPONENT */:\n                result.push(\"0\");\n                break;\n            case \"true\" /* TRUE */:\n                finishWord(\"true\");\n                break;\n            case \"false\" /* FALSE */:\n                finishWord(\"false\");\n                break;\n            case \"null\" /* NULL */:\n                finishWord(\"null\");\n                break;\n            case \"arrayNeedsValue\" /* ARRAY_NEEDS_VALUE */:\n            case \"arrayNeedsComma\" /* ARRAY_NEEDS_COMMA */:\n                result.push(\"]\");\n                break;\n            case \"objectNeedsKey\" /* OBJECT_NEEDS_KEY */:\n            case \"objectNeedsColon\" /* OBJECT_NEEDS_COLON */:\n            case \"objectNeedsValue\" /* OBJECT_NEEDS_VALUE */:\n            case \"objectNeedsComma\" /* OBJECT_NEEDS_COMMA */:\n                result.push(\"}\");\n                break;\n        }\n    }\n    return result.join(\"\");\n}\n//# sourceMappingURL=index.js.map//# sourceURL=[module]\n//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiKHNzcikvLi9ub2RlX21vZHVsZXMvdW50cnVuY2F0ZS1qc29uL2Rpc3QvZXNtL2luZGV4LmpzIiwibWFwcGluZ3MiOiI7Ozs7QUFBQTtBQUNBO0FBQ0E7QUFDZTtBQUNmO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQSxvQ0FBb0M7QUFDcEM7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBLDRCQUE0QjtBQUM1Qiw2Q0FBNkM7QUFDN0M7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0EsbUJBQW1CO0FBQ25CO0FBQ0E7QUFDQTtBQUNBO0FBQ0EsbUNBQW1DLG1CQUFtQjtBQUN0RDtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBLCtCQUErQjtBQUMvQjtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQSwrQkFBK0I7QUFDL0I7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0EsMENBQTBDLFFBQVE7QUFDbEQ7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQSw4QkFBOEI7QUFDOUI7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBIiwic291cmNlcyI6WyIvVXNlcnMvYXBwbGUvRGVza3RvcC9BZWxmIFByb2plY3RzL2FlbGYtY29kZS1nZW5lcmF0b3Ivbm9kZV9tb2R1bGVzL3VudHJ1bmNhdGUtanNvbi9kaXN0L2VzbS9pbmRleC5qcyJdLCJzb3VyY2VzQ29udGVudCI6WyJmdW5jdGlvbiBpc1doaXRlc3BhY2UoY2hhcikge1xuICAgIHJldHVybiBcIlxcdTAwMjBcXHUwMDBEXFx1MDAwQVxcdTAwMDlcIi5pbmRleE9mKGNoYXIpID49IDA7XG59XG5leHBvcnQgZGVmYXVsdCBmdW5jdGlvbiB1bnRydW5jYXRlSnNvbihqc29uKSB7XG4gICAgdmFyIGNvbnRleHRTdGFjayA9IFtcInRvcExldmVsXCIgLyogVE9QX0xFVkVMICovXTtcbiAgICB2YXIgcG9zaXRpb24gPSAwO1xuICAgIHZhciByZXNwYXduUG9zaXRpb247XG4gICAgdmFyIHJlc3Bhd25TdGFja0xlbmd0aDtcbiAgICB2YXIgcmVzcGF3blJlYXNvbjtcbiAgICB2YXIgcHVzaCA9IGZ1bmN0aW9uIChjb250ZXh0KSB7IHJldHVybiBjb250ZXh0U3RhY2sucHVzaChjb250ZXh0KTsgfTtcbiAgICB2YXIgcmVwbGFjZSA9IGZ1bmN0aW9uIChjb250ZXh0KSB7XG4gICAgICAgIHJldHVybiAoY29udGV4dFN0YWNrW2NvbnRleHRTdGFjay5sZW5ndGggLSAxXSA9IGNvbnRleHQpO1xuICAgIH07XG4gICAgdmFyIHNldFJlc3Bhd24gPSBmdW5jdGlvbiAocmVhc29uKSB7XG4gICAgICAgIGlmIChyZXNwYXduUG9zaXRpb24gPT0gbnVsbCkge1xuICAgICAgICAgICAgcmVzcGF3blBvc2l0aW9uID0gcG9zaXRpb247XG4gICAgICAgICAgICByZXNwYXduU3RhY2tMZW5ndGggPSBjb250ZXh0U3RhY2subGVuZ3RoO1xuICAgICAgICAgICAgcmVzcGF3blJlYXNvbiA9IHJlYXNvbjtcbiAgICAgICAgfVxuICAgIH07XG4gICAgdmFyIGNsZWFyUmVzcGF3biA9IGZ1bmN0aW9uIChyZWFzb24pIHtcbiAgICAgICAgaWYgKHJlYXNvbiA9PT0gcmVzcGF3blJlYXNvbikge1xuICAgICAgICAgICAgcmVzcGF3blBvc2l0aW9uID0gdW5kZWZpbmVkO1xuICAgICAgICAgICAgcmVzcGF3blN0YWNrTGVuZ3RoID0gdW5kZWZpbmVkO1xuICAgICAgICAgICAgcmVzcGF3blJlYXNvbiA9IHVuZGVmaW5lZDtcbiAgICAgICAgfVxuICAgIH07XG4gICAgdmFyIHBvcCA9IGZ1bmN0aW9uICgpIHsgcmV0dXJuIGNvbnRleHRTdGFjay5wb3AoKTsgfTtcbiAgICB2YXIgZG9udENvbnN1bWVDaGFyYWN0ZXIgPSBmdW5jdGlvbiAoKSB7IHJldHVybiBwb3NpdGlvbi0tOyB9O1xuICAgIHZhciBzdGFydEFueSA9IGZ1bmN0aW9uIChjaGFyKSB7XG4gICAgICAgIGlmIChcIjBcIiA8PSBjaGFyICYmIGNoYXIgPD0gXCI5XCIpIHtcbiAgICAgICAgICAgIHB1c2goXCJudW1iZXJcIiAvKiBOVU1CRVIgKi8pO1xuICAgICAgICAgICAgcmV0dXJuO1xuICAgICAgICB9XG4gICAgICAgIHN3aXRjaCAoY2hhcikge1xuICAgICAgICAgICAgY2FzZSAnXCInOlxuICAgICAgICAgICAgICAgIHB1c2goXCJzdHJpbmdcIiAvKiBTVFJJTkcgKi8pO1xuICAgICAgICAgICAgICAgIHJldHVybjtcbiAgICAgICAgICAgIGNhc2UgXCItXCI6XG4gICAgICAgICAgICAgICAgcHVzaChcIm51bWJlck5lZWRzRGlnaXRcIiAvKiBOVU1CRVJfTkVFRFNfRElHSVQgKi8pO1xuICAgICAgICAgICAgICAgIHJldHVybjtcbiAgICAgICAgICAgIGNhc2UgXCJ0XCI6XG4gICAgICAgICAgICAgICAgcHVzaChcInRydWVcIiAvKiBUUlVFICovKTtcbiAgICAgICAgICAgICAgICByZXR1cm47XG4gICAgICAgICAgICBjYXNlIFwiZlwiOlxuICAgICAgICAgICAgICAgIHB1c2goXCJmYWxzZVwiIC8qIEZBTFNFICovKTtcbiAgICAgICAgICAgICAgICByZXR1cm47XG4gICAgICAgICAgICBjYXNlIFwiblwiOlxuICAgICAgICAgICAgICAgIHB1c2goXCJudWxsXCIgLyogTlVMTCAqLyk7XG4gICAgICAgICAgICAgICAgcmV0dXJuO1xuICAgICAgICAgICAgY2FzZSBcIltcIjpcbiAgICAgICAgICAgICAgICBwdXNoKFwiYXJyYXlOZWVkc1ZhbHVlXCIgLyogQVJSQVlfTkVFRFNfVkFMVUUgKi8pO1xuICAgICAgICAgICAgICAgIHJldHVybjtcbiAgICAgICAgICAgIGNhc2UgXCJ7XCI6XG4gICAgICAgICAgICAgICAgcHVzaChcIm9iamVjdE5lZWRzS2V5XCIgLyogT0JKRUNUX05FRURTX0tFWSAqLyk7XG4gICAgICAgICAgICAgICAgcmV0dXJuO1xuICAgICAgICB9XG4gICAgfTtcbiAgICBmb3IgKHZhciBsZW5ndGggPSBqc29uLmxlbmd0aDsgcG9zaXRpb24gPCBsZW5ndGg7IHBvc2l0aW9uKyspIHtcbiAgICAgICAgdmFyIGNoYXIgPSBqc29uW3Bvc2l0aW9uXTtcbiAgICAgICAgc3dpdGNoIChjb250ZXh0U3RhY2tbY29udGV4dFN0YWNrLmxlbmd0aCAtIDFdKSB7XG4gICAgICAgICAgICBjYXNlIFwidG9wTGV2ZWxcIiAvKiBUT1BfTEVWRUwgKi86XG4gICAgICAgICAgICAgICAgc3RhcnRBbnkoY2hhcik7XG4gICAgICAgICAgICAgICAgYnJlYWs7XG4gICAgICAgICAgICBjYXNlIFwic3RyaW5nXCIgLyogU1RSSU5HICovOlxuICAgICAgICAgICAgICAgIHN3aXRjaCAoY2hhcikge1xuICAgICAgICAgICAgICAgICAgICBjYXNlICdcIic6XG4gICAgICAgICAgICAgICAgICAgICAgICBwb3AoKTtcbiAgICAgICAgICAgICAgICAgICAgICAgIGJyZWFrO1xuICAgICAgICAgICAgICAgICAgICBjYXNlIFwiXFxcXFwiOlxuICAgICAgICAgICAgICAgICAgICAgICAgc2V0UmVzcGF3bihcInN0cmluZ0VzY2FwZVwiIC8qIFNUUklOR19FU0NBUEUgKi8pO1xuICAgICAgICAgICAgICAgICAgICAgICAgcHVzaChcInN0cmluZ0VzY2FwZWRcIiAvKiBTVFJJTkdfRVNDQVBFRCAqLyk7XG4gICAgICAgICAgICAgICAgICAgICAgICBicmVhaztcbiAgICAgICAgICAgICAgICB9XG4gICAgICAgICAgICAgICAgYnJlYWs7XG4gICAgICAgICAgICBjYXNlIFwic3RyaW5nRXNjYXBlZFwiIC8qIFNUUklOR19FU0NBUEVEICovOlxuICAgICAgICAgICAgICAgIGlmIChjaGFyID09PSBcInVcIikge1xuICAgICAgICAgICAgICAgICAgICBwdXNoKFwic3RyaW5nVW5pY29kZVwiIC8qIFNUUklOR19VTklDT0RFICovKTtcbiAgICAgICAgICAgICAgICB9XG4gICAgICAgICAgICAgICAgZWxzZSB7XG4gICAgICAgICAgICAgICAgICAgIGNsZWFyUmVzcGF3bihcInN0cmluZ0VzY2FwZVwiIC8qIFNUUklOR19FU0NBUEUgKi8pO1xuICAgICAgICAgICAgICAgICAgICBwb3AoKTtcbiAgICAgICAgICAgICAgICB9XG4gICAgICAgICAgICAgICAgYnJlYWs7XG4gICAgICAgICAgICBjYXNlIFwic3RyaW5nVW5pY29kZVwiIC8qIFNUUklOR19VTklDT0RFICovOlxuICAgICAgICAgICAgICAgIGlmIChwb3NpdGlvbiAtIGpzb24ubGFzdEluZGV4T2YoXCJ1XCIsIHBvc2l0aW9uKSA9PT0gNCkge1xuICAgICAgICAgICAgICAgICAgICBjbGVhclJlc3Bhd24oXCJzdHJpbmdFc2NhcGVcIiAvKiBTVFJJTkdfRVNDQVBFICovKTtcbiAgICAgICAgICAgICAgICAgICAgcG9wKCk7XG4gICAgICAgICAgICAgICAgfVxuICAgICAgICAgICAgICAgIGJyZWFrO1xuICAgICAgICAgICAgY2FzZSBcIm51bWJlclwiIC8qIE5VTUJFUiAqLzpcbiAgICAgICAgICAgICAgICBpZiAoY2hhciA9PT0gXCIuXCIpIHtcbiAgICAgICAgICAgICAgICAgICAgcmVwbGFjZShcIm51bWJlck5lZWRzRGlnaXRcIiAvKiBOVU1CRVJfTkVFRFNfRElHSVQgKi8pO1xuICAgICAgICAgICAgICAgIH1cbiAgICAgICAgICAgICAgICBlbHNlIGlmIChjaGFyID09PSBcImVcIiB8fCBjaGFyID09PSBcIkVcIikge1xuICAgICAgICAgICAgICAgICAgICByZXBsYWNlKFwibnVtYmVyTmVlZHNFeHBvbmVudFwiIC8qIE5VTUJFUl9ORUVEU19FWFBPTkVOVCAqLyk7XG4gICAgICAgICAgICAgICAgfVxuICAgICAgICAgICAgICAgIGVsc2UgaWYgKGNoYXIgPCBcIjBcIiB8fCBjaGFyID4gXCI5XCIpIHtcbiAgICAgICAgICAgICAgICAgICAgZG9udENvbnN1bWVDaGFyYWN0ZXIoKTtcbiAgICAgICAgICAgICAgICAgICAgcG9wKCk7XG4gICAgICAgICAgICAgICAgfVxuICAgICAgICAgICAgICAgIGJyZWFrO1xuICAgICAgICAgICAgY2FzZSBcIm51bWJlck5lZWRzRGlnaXRcIiAvKiBOVU1CRVJfTkVFRFNfRElHSVQgKi86XG4gICAgICAgICAgICAgICAgcmVwbGFjZShcIm51bWJlclwiIC8qIE5VTUJFUiAqLyk7XG4gICAgICAgICAgICAgICAgYnJlYWs7XG4gICAgICAgICAgICBjYXNlIFwibnVtYmVyTmVlZHNFeHBvbmVudFwiIC8qIE5VTUJFUl9ORUVEU19FWFBPTkVOVCAqLzpcbiAgICAgICAgICAgICAgICBpZiAoY2hhciA9PT0gXCIrXCIgfHwgY2hhciA9PT0gXCItXCIpIHtcbiAgICAgICAgICAgICAgICAgICAgcmVwbGFjZShcIm51bWJlck5lZWRzRGlnaXRcIiAvKiBOVU1CRVJfTkVFRFNfRElHSVQgKi8pO1xuICAgICAgICAgICAgICAgIH1cbiAgICAgICAgICAgICAgICBlbHNlIHtcbiAgICAgICAgICAgICAgICAgICAgcmVwbGFjZShcIm51bWJlclwiIC8qIE5VTUJFUiAqLyk7XG4gICAgICAgICAgICAgICAgfVxuICAgICAgICAgICAgICAgIGJyZWFrO1xuICAgICAgICAgICAgY2FzZSBcInRydWVcIiAvKiBUUlVFICovOlxuICAgICAgICAgICAgY2FzZSBcImZhbHNlXCIgLyogRkFMU0UgKi86XG4gICAgICAgICAgICBjYXNlIFwibnVsbFwiIC8qIE5VTEwgKi86XG4gICAgICAgICAgICAgICAgaWYgKGNoYXIgPCBcImFcIiB8fCBjaGFyID4gXCJ6XCIpIHtcbiAgICAgICAgICAgICAgICAgICAgZG9udENvbnN1bWVDaGFyYWN0ZXIoKTtcbiAgICAgICAgICAgICAgICAgICAgcG9wKCk7XG4gICAgICAgICAgICAgICAgfVxuICAgICAgICAgICAgICAgIGJyZWFrO1xuICAgICAgICAgICAgY2FzZSBcImFycmF5TmVlZHNWYWx1ZVwiIC8qIEFSUkFZX05FRURTX1ZBTFVFICovOlxuICAgICAgICAgICAgICAgIGlmIChjaGFyID09PSBcIl1cIikge1xuICAgICAgICAgICAgICAgICAgICBwb3AoKTtcbiAgICAgICAgICAgICAgICB9XG4gICAgICAgICAgICAgICAgZWxzZSBpZiAoIWlzV2hpdGVzcGFjZShjaGFyKSkge1xuICAgICAgICAgICAgICAgICAgICBjbGVhclJlc3Bhd24oXCJjb2xsZWN0aW9uSXRlbVwiIC8qIENPTExFQ1RJT05fSVRFTSAqLyk7XG4gICAgICAgICAgICAgICAgICAgIHJlcGxhY2UoXCJhcnJheU5lZWRzQ29tbWFcIiAvKiBBUlJBWV9ORUVEU19DT01NQSAqLyk7XG4gICAgICAgICAgICAgICAgICAgIHN0YXJ0QW55KGNoYXIpO1xuICAgICAgICAgICAgICAgIH1cbiAgICAgICAgICAgICAgICBicmVhaztcbiAgICAgICAgICAgIGNhc2UgXCJhcnJheU5lZWRzQ29tbWFcIiAvKiBBUlJBWV9ORUVEU19DT01NQSAqLzpcbiAgICAgICAgICAgICAgICBpZiAoY2hhciA9PT0gXCJdXCIpIHtcbiAgICAgICAgICAgICAgICAgICAgcG9wKCk7XG4gICAgICAgICAgICAgICAgfVxuICAgICAgICAgICAgICAgIGVsc2UgaWYgKGNoYXIgPT09IFwiLFwiKSB7XG4gICAgICAgICAgICAgICAgICAgIHNldFJlc3Bhd24oXCJjb2xsZWN0aW9uSXRlbVwiIC8qIENPTExFQ1RJT05fSVRFTSAqLyk7XG4gICAgICAgICAgICAgICAgICAgIHJlcGxhY2UoXCJhcnJheU5lZWRzVmFsdWVcIiAvKiBBUlJBWV9ORUVEU19WQUxVRSAqLyk7XG4gICAgICAgICAgICAgICAgfVxuICAgICAgICAgICAgICAgIGJyZWFrO1xuICAgICAgICAgICAgY2FzZSBcIm9iamVjdE5lZWRzS2V5XCIgLyogT0JKRUNUX05FRURTX0tFWSAqLzpcbiAgICAgICAgICAgICAgICBpZiAoY2hhciA9PT0gXCJ9XCIpIHtcbiAgICAgICAgICAgICAgICAgICAgcG9wKCk7XG4gICAgICAgICAgICAgICAgfVxuICAgICAgICAgICAgICAgIGVsc2UgaWYgKGNoYXIgPT09ICdcIicpIHtcbiAgICAgICAgICAgICAgICAgICAgc2V0UmVzcGF3bihcImNvbGxlY3Rpb25JdGVtXCIgLyogQ09MTEVDVElPTl9JVEVNICovKTtcbiAgICAgICAgICAgICAgICAgICAgcmVwbGFjZShcIm9iamVjdE5lZWRzQ29sb25cIiAvKiBPQkpFQ1RfTkVFRFNfQ09MT04gKi8pO1xuICAgICAgICAgICAgICAgICAgICBwdXNoKFwic3RyaW5nXCIgLyogU1RSSU5HICovKTtcbiAgICAgICAgICAgICAgICB9XG4gICAgICAgICAgICAgICAgYnJlYWs7XG4gICAgICAgICAgICBjYXNlIFwib2JqZWN0TmVlZHNDb2xvblwiIC8qIE9CSkVDVF9ORUVEU19DT0xPTiAqLzpcbiAgICAgICAgICAgICAgICBpZiAoY2hhciA9PT0gXCI6XCIpIHtcbiAgICAgICAgICAgICAgICAgICAgcmVwbGFjZShcIm9iamVjdE5lZWRzVmFsdWVcIiAvKiBPQkpFQ1RfTkVFRFNfVkFMVUUgKi8pO1xuICAgICAgICAgICAgICAgIH1cbiAgICAgICAgICAgICAgICBicmVhaztcbiAgICAgICAgICAgIGNhc2UgXCJvYmplY3ROZWVkc1ZhbHVlXCIgLyogT0JKRUNUX05FRURTX1ZBTFVFICovOlxuICAgICAgICAgICAgICAgIGlmICghaXNXaGl0ZXNwYWNlKGNoYXIpKSB7XG4gICAgICAgICAgICAgICAgICAgIGNsZWFyUmVzcGF3bihcImNvbGxlY3Rpb25JdGVtXCIgLyogQ09MTEVDVElPTl9JVEVNICovKTtcbiAgICAgICAgICAgICAgICAgICAgcmVwbGFjZShcIm9iamVjdE5lZWRzQ29tbWFcIiAvKiBPQkpFQ1RfTkVFRFNfQ09NTUEgKi8pO1xuICAgICAgICAgICAgICAgICAgICBzdGFydEFueShjaGFyKTtcbiAgICAgICAgICAgICAgICB9XG4gICAgICAgICAgICAgICAgYnJlYWs7XG4gICAgICAgICAgICBjYXNlIFwib2JqZWN0TmVlZHNDb21tYVwiIC8qIE9CSkVDVF9ORUVEU19DT01NQSAqLzpcbiAgICAgICAgICAgICAgICBpZiAoY2hhciA9PT0gXCJ9XCIpIHtcbiAgICAgICAgICAgICAgICAgICAgcG9wKCk7XG4gICAgICAgICAgICAgICAgfVxuICAgICAgICAgICAgICAgIGVsc2UgaWYgKGNoYXIgPT09IFwiLFwiKSB7XG4gICAgICAgICAgICAgICAgICAgIHNldFJlc3Bhd24oXCJjb2xsZWN0aW9uSXRlbVwiIC8qIENPTExFQ1RJT05fSVRFTSAqLyk7XG4gICAgICAgICAgICAgICAgICAgIHJlcGxhY2UoXCJvYmplY3ROZWVkc0tleVwiIC8qIE9CSkVDVF9ORUVEU19LRVkgKi8pO1xuICAgICAgICAgICAgICAgIH1cbiAgICAgICAgICAgICAgICBicmVhaztcbiAgICAgICAgfVxuICAgIH1cbiAgICBpZiAocmVzcGF3blN0YWNrTGVuZ3RoICE9IG51bGwpIHtcbiAgICAgICAgY29udGV4dFN0YWNrLmxlbmd0aCA9IHJlc3Bhd25TdGFja0xlbmd0aDtcbiAgICB9XG4gICAgdmFyIHJlc3VsdCA9IFtcbiAgICAgICAgcmVzcGF3blBvc2l0aW9uICE9IG51bGwgPyBqc29uLnNsaWNlKDAsIHJlc3Bhd25Qb3NpdGlvbikgOiBqc29uLFxuICAgIF07XG4gICAgdmFyIGZpbmlzaFdvcmQgPSBmdW5jdGlvbiAod29yZCkge1xuICAgICAgICByZXR1cm4gcmVzdWx0LnB1c2god29yZC5zbGljZShqc29uLmxlbmd0aCAtIGpzb24ubGFzdEluZGV4T2Yod29yZFswXSkpKTtcbiAgICB9O1xuICAgIGZvciAodmFyIGkgPSBjb250ZXh0U3RhY2subGVuZ3RoIC0gMTsgaSA+PSAwOyBpLS0pIHtcbiAgICAgICAgc3dpdGNoIChjb250ZXh0U3RhY2tbaV0pIHtcbiAgICAgICAgICAgIGNhc2UgXCJzdHJpbmdcIiAvKiBTVFJJTkcgKi86XG4gICAgICAgICAgICAgICAgcmVzdWx0LnB1c2goJ1wiJyk7XG4gICAgICAgICAgICAgICAgYnJlYWs7XG4gICAgICAgICAgICBjYXNlIFwibnVtYmVyTmVlZHNEaWdpdFwiIC8qIE5VTUJFUl9ORUVEU19ESUdJVCAqLzpcbiAgICAgICAgICAgIGNhc2UgXCJudW1iZXJOZWVkc0V4cG9uZW50XCIgLyogTlVNQkVSX05FRURTX0VYUE9ORU5UICovOlxuICAgICAgICAgICAgICAgIHJlc3VsdC5wdXNoKFwiMFwiKTtcbiAgICAgICAgICAgICAgICBicmVhaztcbiAgICAgICAgICAgIGNhc2UgXCJ0cnVlXCIgLyogVFJVRSAqLzpcbiAgICAgICAgICAgICAgICBmaW5pc2hXb3JkKFwidHJ1ZVwiKTtcbiAgICAgICAgICAgICAgICBicmVhaztcbiAgICAgICAgICAgIGNhc2UgXCJmYWxzZVwiIC8qIEZBTFNFICovOlxuICAgICAgICAgICAgICAgIGZpbmlzaFdvcmQoXCJmYWxzZVwiKTtcbiAgICAgICAgICAgICAgICBicmVhaztcbiAgICAgICAgICAgIGNhc2UgXCJudWxsXCIgLyogTlVMTCAqLzpcbiAgICAgICAgICAgICAgICBmaW5pc2hXb3JkKFwibnVsbFwiKTtcbiAgICAgICAgICAgICAgICBicmVhaztcbiAgICAgICAgICAgIGNhc2UgXCJhcnJheU5lZWRzVmFsdWVcIiAvKiBBUlJBWV9ORUVEU19WQUxVRSAqLzpcbiAgICAgICAgICAgIGNhc2UgXCJhcnJheU5lZWRzQ29tbWFcIiAvKiBBUlJBWV9ORUVEU19DT01NQSAqLzpcbiAgICAgICAgICAgICAgICByZXN1bHQucHVzaChcIl1cIik7XG4gICAgICAgICAgICAgICAgYnJlYWs7XG4gICAgICAgICAgICBjYXNlIFwib2JqZWN0TmVlZHNLZXlcIiAvKiBPQkpFQ1RfTkVFRFNfS0VZICovOlxuICAgICAgICAgICAgY2FzZSBcIm9iamVjdE5lZWRzQ29sb25cIiAvKiBPQkpFQ1RfTkVFRFNfQ09MT04gKi86XG4gICAgICAgICAgICBjYXNlIFwib2JqZWN0TmVlZHNWYWx1ZVwiIC8qIE9CSkVDVF9ORUVEU19WQUxVRSAqLzpcbiAgICAgICAgICAgIGNhc2UgXCJvYmplY3ROZWVkc0NvbW1hXCIgLyogT0JKRUNUX05FRURTX0NPTU1BICovOlxuICAgICAgICAgICAgICAgIHJlc3VsdC5wdXNoKFwifVwiKTtcbiAgICAgICAgICAgICAgICBicmVhaztcbiAgICAgICAgfVxuICAgIH1cbiAgICByZXR1cm4gcmVzdWx0LmpvaW4oXCJcIik7XG59XG4vLyMgc291cmNlTWFwcGluZ1VSTD1pbmRleC5qcy5tYXAiXSwibmFtZXMiOltdLCJpZ25vcmVMaXN0IjpbMF0sInNvdXJjZVJvb3QiOiIifQ==\n//# sourceURL=webpack-internal:///(ssr)/./node_modules/untruncate-json/dist/esm/index.js\n");

/***/ })

};
;