angular
    .module('monitoring.services', [])
    .factory('monExpressionBuilder', expressionBuilder);

function expressionBuilder() {

    return {
        asString: subExpressionToString
    };

    function subExpressionToString(subExpressions) {
        var tmp = [];
        angular.forEach(subExpressions, function(expr) {

            if ('op' in expr) {
                tmp.push(' ');
                tmp.push(expr['op']);
                tmp.push(' ');
            }

            tmp.push([
                expr.fun,
                '(',
                expr.metric ? expr.metric.name : '?', '{', expr.dimensions.join(','), '}',
                (expr.deterministic ? ',deterministic': ''),
                ')',
                expr.cmp,
                expr.threshold
            ].join(''));
        });
        return tmp.join(subExpressions.length > 1 ? '\n' : '');
    }

}
