// export interface Namespace {
//     id: number;
//     name: string;
//     root_directories: Directory[];
// }
//
// export interface Directory {
//     id: number;
//     name: string;
//     parent: number | null;
//     children: Directory[];
// }
export interface Namespace {
    id: number
    name: string
    description: string | null
    created_at: string
    updated_at: string
}

export interface Directory {
    id: number
    name: string
    namespace: number
    parent: number | null
    full_path: string
    created_at: string
    updated_at: string
    children?: Directory[]
    notes?: Note[]
}

// export enum CategoryType {
//     NORMAL = 'normal',
//     DATABASE = 'database',
//     TOOL = 'tool'
// }

export const CategoryType = {
    NORMAL: 'normal',
    DATABASE: 'database',
    TOOL: 'tool',
} as const;

export type CategoryType = (typeof CategoryType)[keyof typeof CategoryType];

export interface Note {
    id: number
    title: string
    content: string
    directory: number
    category: CategoryType  // 新增类型字段
    created_at: string
    updated_at: string
}

export interface DirectoryBase {
    id: number;
    name: string;
    namespace: number;
    parent: number | null;
    full_path: string;
    created_at: string;
    updated_at: string;
}

// 用于目录树结构的特殊类型
export interface DirectoryTreeItem extends DirectoryBase {
    children?: DirectoryTreeItem[];
    notes?: Note[];
}

export interface Directory extends DirectoryBase {
    // 普通目录接口不需要 children 和 notes
}

