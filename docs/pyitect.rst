pyitect package
===============

Submodules
----------

.. toctree::

   pyitect.imports

Module contents
---------------

.. automodule:: pyitect
    :members:
    :undoc-members:

    .. class:: Version

        Version class imported directly from `semantic_version`

        see the `python-semanticversion <https://github.com/rbarrois/python-semanticversion>`_
        project for more information.

    .. class:: Spec

        Spec class imported directly from `semantic_version`

        see the `python-semanticversion <https://github.com/rbarrois/python-semanticversion>`_
        project for more information.

    .. autoclass:: System
        :members:
        :undoc-members:

    .. autoclass:: Plugin
        :members:
        :undoc-members:

    .. autoclass:: Component
        :members:
        :undoc-members:

    .. autofunction:: get_system

    .. autofunction:: build_system

    .. autofunction:: destroy_system


    .. autofunction:: issubcomponent

    .. autofunction:: get_unique_name

    .. autofunction:: gen_version

    .. autofunction:: expand_version_req

    
    .. autoexception:: PyitectError

    .. autoexception:: PyitectNotProvidedError

    .. autoexception:: PyitectNotMetError

    .. autoexception:: PyitectLoadError

    .. autoexception:: PyitectOnEnableError

    .. autoexception:: PyitectDupError
