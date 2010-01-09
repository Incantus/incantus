This event dispatch code is derived from PyDispatcher <http://pydispatcher.sf.net> 
(BSD licensed - see license.txt)

There are quite a few modifications to support the requirements for Incantus 
(such as reentrant dispatching, automatic expiry after receiving N signals, 
and some others). Also the robustApply function is reused in modified form  
to allow matching condition functions to events for triggered abilities.
