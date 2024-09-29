from sqlalchemy import select
from dooit.api.exceptions import NoParentError, MultipleParentError
from tests.test_core.core_base import CoreTestBase
from dooit.api import Todo, Workspace


class TestTodo(CoreTestBase):
    def setUp(self):
        super().setUp()
        self.default_workspace = Workspace()

    def test_todo_creation(self):
        for _ in range(5):
            todo = Todo(parent_workspace=self.default_workspace)
            todo.save()

        result = Todo.all()
        self.assertEqual(len(result), 5)

        indexs = sorted([t.order_index for t in result])

        self.assertEqual(indexs, [0, 1, 2, 3, 4])

    def test_sibling_methods(self):
        for _ in range(5):
            todo = Todo(parent_workspace=self.default_workspace)
            todo.save()

        query = select(Todo)
        todo = self.session.execute(query).scalars().first()

        assert todo is not None

        siblings = todo.siblings
        index_ids = [w.order_index for w in siblings]
        self.assertEqual(index_ids, [0, 1, 2, 3, 4])
        self.assertTrue(siblings[0].is_first_sibling())
        self.assertTrue(siblings[-1].is_last_sibling())

    def test_todo_siblings_by_creation(self):
        for _ in range(5):
            todo = Todo(parent_workspace=self.default_workspace)
            todo.save()

        query = select(Todo)
        workspace = self.session.execute(query).scalars().first()

        assert workspace is not None
        self.assertEqual(len(workspace.siblings), 5)

    def test_parent_kind(self):
        todo = Todo(parent_workspace=self.default_workspace)
        todo.save()

        self.assertFalse(todo.has_same_parent_kind)

        todo2 = Todo(parent_todo=todo)
        todo2.save()

        self.assertTrue(todo2.has_same_parent_kind)

    def test_without_parent(self):
        todo = Todo()

        with self.assertRaises(NoParentError):
            todo.save()

    def test_with_both_parents(self):
        w = self.default_workspace
        t = w.add_todo()

        todo = Todo(parent_workspace=w, parent_todo=t)

        with self.assertRaises(MultipleParentError):
            todo.save()

    def test_sibling_add(self):
        t = self.default_workspace.add_todo()
        self.default_workspace.add_todo()

        t2 = t.add_sibling()

        self.assertEqual(len(t.siblings), 3)
        self.assertEqual(len(t2.siblings), 3)
        self.assertEqual(t2.order_index, 1)

    def test_comparable_fields(self):
        fields = Todo.comparable_fields()
        expected_fields = [
            "description",
            "due",
            "effort",
            "recurrence",
            "urgency",
            "pending",
        ]
        self.assertEqual(fields, expected_fields)

    def test_nest_level(self):

        t = self.default_workspace.add_todo()
        self.assertEqual(t.nest_level, 0)

        t = t.add_todo()
        self.assertEqual(t.nest_level, 1)

        t = t.add_todo()
        self.assertEqual(t.nest_level, 2)

    def test_from_id(self):
        t = self.default_workspace.add_todo()
        _id = t.id
        t_from_id = Todo.from_id(str(_id))

        self.assertEqual(t_from_id, t)

    def test_toggle_complete(self):
        t = self.default_workspace.add_todo()
        self.assertTrue(t.pending)

        t.toggle_complete()
        self.assertFalse(t.pending)

