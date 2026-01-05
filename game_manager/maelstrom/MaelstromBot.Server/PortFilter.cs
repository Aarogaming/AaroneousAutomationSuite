using Microsoft.AspNetCore.Http;

namespace MaelstromBot.Server;

public sealed class PortFilter : IEndpointFilter
{
    private readonly int _allowedPort;
    public PortFilter(int allowedPort) => _allowedPort = allowedPort;

    public ValueTask<object?> InvokeAsync(EndpointFilterInvocationContext context, EndpointFilterDelegate next)
    {
        if (context.HttpContext.Connection.LocalPort != _allowedPort)
        {
            return ValueTask.FromResult<object?>(Results.NotFound());
        }

        return next(context);
    }
}
