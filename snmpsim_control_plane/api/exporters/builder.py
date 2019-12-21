#
# This file is part of SNMP simulator Control Plane software.
#
# Copyright (c) 2010-2019, Ilya Etingof <etingof@gmail.com>
# License: http://snmplabs.com/snmpsim/license.html
#
# SNMP simulator management: turn ORM data into a tree of dicts
#
from sqlalchemy import inspect

from snmpsim_control_plane.api.models import mgmt as models


def object_as_dict(obj):
    return {
        c.key: getattr(obj, c.key)
        for c in inspect(obj).mapper.column_attrs
    }


def to_dict():
    labs = []

    context = {
        'labs': labs
    }

    query = (
        models.Lab
        .query
        .filter_by(power='on').all()
    )

    for orm_lab in query:
        agents = []

        lab = object_as_dict(orm_lab)
        lab.update(agents=agents)
        labs.append(lab)

        query = (
            models.Agent
            .query
            .outerjoin(models.LabAgent)
            .all()
        )

        for orm_agent in query:
            engines = []
            selectors = []

            agent = object_as_dict(orm_agent)
            agent.update(engines=engines, selectors=selectors)
            agents.append(agent)

            query = (
                models.Engine
                .query
                .outerjoin(models.AgentEngine)
                .all()
            )

            for orm_engine in query:
                users = []
                endpoints = []

                engine = object_as_dict(orm_engine)
                engine.update(users=users, endpoints=endpoints)
                engines.append(engine)

                query = (
                    models.User
                    .query
                    .outerjoin(models.EngineUser)
                    .all()
                )

                for orm_user in query:
                    user = object_as_dict(orm_user)
                    users.append(user)

                query = (
                    models.Endpoint
                    .query
                    .outerjoin(models.EngineEndpoint)
                    .all()
                )

                for orm_endpoint in query:
                    endpoint = object_as_dict(orm_endpoint)
                    endpoints.append(endpoint)

            query = (
                models.Selector
                .query
                .outerjoin(models.AgentSelector)
                .all()
            )

            for orm_selector in query:
                selector = object_as_dict(orm_selector)
                selectors.append(selector)

    return context
