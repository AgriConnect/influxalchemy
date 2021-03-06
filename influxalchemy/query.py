""" InfluxDB Query Object. """

import functools

from . import meta


class InfluxDBQuery(object):
    """ InfluxDB Query object.

        entities    (tuple):          Query entities
        client      (InfluxAlchemy):  InfluxAlchemy instance
        expressions (tuple):          Query filters
        groupby     (str):            GROUP BY string
    """
    def __init__(self, entities, client, expressions=None, groupby=None):
        self._entities = entities
        self._client = client
        self._expressions = expressions or ()
        self._groupby = groupby

    def __str__(self):
        select = ", ".join(self._select)
        from_ = self._from
        where = " AND ".join(self._where)
        if any(where):
            iql = "SELECT %s FROM %s WHERE %s" % (select, from_, where)
        else:
            iql = "SELECT %s FROM %s" % (select, from_)
        if self._groupby is not None:
            iql += " GROUP BY %s" % self._groupby
        return "%s;" % iql

    def __repr__(self):
        return str(self)

    def execute(self):
        """ Execute query. """
        return self._client.bind.query(str(self))

    def filter(self, *expressions):
        """ Filter query. """
        expressions = self._expressions + expressions
        return InfluxDBQuery(self._entities, self._client, expressions)

    def filter_by(self, **kwargs):
        """ Filter query by tag value. """
        expressions = self._expressions
        for key, val in kwargs.items():
            expressions += meta.TagExp.equals(key, val),
        return InfluxDBQuery(self._entities, self._client, expressions)

    def group_by(self, groupby):
        """ Group query. """
        return InfluxDBQuery(
            self._entities, self._client, self._expressions, groupby)

    @property
    def measurement(self):
        """ Query measurement. """
        measurements = set(x.measurement for x in self._entities)
        return functools.reduce(lambda x, y: x | y, measurements)

    @property
    def _select(self):
        """ SELECT statement. """
        selects = []
        for ent in self._entities:
            # Entity is a Tag
            if isinstance(ent, meta.Tag):
                selects.append(str(ent))
            # Entity is a Measurement
            else:
                try:
                    for tag in self._client.tags(ent):
                        selects.append(tag)
                    for field in self._client.fields(ent):
                        selects.append(field)
                # pylint: disable=bare-except
                except:
                    pass
        if not selects:
            selects = ["*"]
        return selects

    @property
    def _from(self):
        """ FROM statement. """
        return str(self.measurement)

    @property
    def _where(self):
        """ WHERE statement. """
        for exp in self._expressions:
            yield "(%s)" % exp
