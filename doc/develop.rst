Extending Carmen
================

Carmen can be extended with user-written resolvers.
These resolvers should be subclasses of
:py:class:`carmen.resolver.AbstractResolver`
that provide implementations of
the :py:meth:`.add_location` and :py:meth:`.resolve_tweet` methods.
Resolvers may create lookup tables or other caches when locations are
added, depending on how they resolve individual tweets.

Using custom resolvers with the :py:func:`.get_resolver` API
is a two-step process.
First, the resolver should be decorated with the
:py:func:`carmen.resolver.register`
function, in order to enable automatic loading.
The decorator takes one argument,
a name that is used to refer to the resolver
for inclusion, exclusion, option specification,
and in :py:attr:`.resolution_method` attributes::

    from carmen.resolver import AbstractResolver, register

    @register('foo')
    class FooResolver(AbstractResolver):
        ...

Next, when calling :py:func:`.get_resolver`,
specify modules containing additional custom resolvers
in the *modules* keyword argument::

    from carmen import get_resolver
    import mypackage.resolvers

    resolver = get_resolver(modules=[mypackage.resolvers])

Any options specified in the *options* argument
to :py:func:`.get_resolver` are passed as keyword arguments
when the resolver is instantiated.
For example, a resolver named ``custom`` may have the following
signature for its ``__init__`` method::

    def __init__(self, allow_foo=True, allow_bar=False):
        ...

These defaults may be overridden
with an *options* dictionary containing::

    {'custom': {'allow_foo': False, 'allow_bar': True}}

Locations may then be added, and tweets resolved, as with Carmen's
built-in resolvers.
