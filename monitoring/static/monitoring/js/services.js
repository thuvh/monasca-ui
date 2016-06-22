angular
    .module('monitoring.services', [])
    .factory('monExpressionBuilder', expressionBuilder);

function expressionBuilder() {

    return {
        asString: subExpressionToString
    };

    function subExpressionToString(subExpressions, withOp) {
        var tmp = [];
        var exprAsStr;
        angular.forEach(subExpressions, function(expr) {
            exprAsStr = [
                expr.fun,
                '(',
                expr.metric ? expr.metric.name : '?', '{', expr.dimensions.join(','), '}',
                (expr.deterministic ? ',deterministic': ''),
                ')',
                expr.cmp,
                expr.threshold,
                withOp ? renderOp(expr) : ''
            ].join('');
            tmp.push(exprAsStr);
        });
        return tmp.join(subExpressions.length > 1 ? '\n' : '');
    }

    function renderOp(expr) {
        var tmp = [];
        if ('op' in expr) {
            tmp.push(' ');
            tmp.push(expr['op']);
            tmp.push(' ');
        }
        return tmp.join('');
    }
}
