'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import { useAccountTypes, useAssetTypes, useLiabilityTypes, useCategories } from '@/lib/api/queries/reference';

export default function ReferencePage() {
  const accountTypes = useAccountTypes();
  const assetTypes = useAssetTypes();
  const liabilityTypes = useLiabilityTypes();
  const categories = useCategories();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Справочники</h1>
        <p className="text-gray-500">Типы счетов, активов, обязательств и категории</p>
      </div>

      <Tabs defaultValue="account-types" className="space-y-4">
        <TabsList>
          <TabsTrigger value="account-types">Типы счетов</TabsTrigger>
          <TabsTrigger value="asset-types">Типы активов</TabsTrigger>
          <TabsTrigger value="liability-types">Типы обязательств</TabsTrigger>
          <TabsTrigger value="categories">Категории</TabsTrigger>
        </TabsList>

        <TabsContent value="account-types">
          <Card>
            <CardHeader><CardTitle>Типы счетов</CardTitle></CardHeader>
            <CardContent>
              {accountTypes.isLoading && <div className="space-y-2">{[1,2,3].map(i=><Skeleton key={i} className="h-10 w-full"/>)}</div>}
              {accountTypes.isError && <div className="text-red-500">Ошибка загрузки</div>}
              {accountTypes.data?.map((item) => (
                <div key={item.id} className="p-3 border-b last:border-0 flex justify-between text-sm">
                  <span className="font-medium">{item.name}</span>
                  <span className="text-gray-500">{item.id}</span>
                </div>
              ))}
              {accountTypes.data?.length === 0 && <div className="text-gray-500 py-4">Пусто</div>}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="asset-types">
          <Card>
            <CardHeader><CardTitle>Типы активов</CardTitle></CardHeader>
            <CardContent>
              {assetTypes.isLoading && <div className="space-y-2">{[1,2,3].map(i=><Skeleton key={i} className="h-10 w-full"/>)}</div>}
              {assetTypes.isError && <div className="text-red-500">Ошибка загрузки</div>}
              {assetTypes.data?.map((item) => (
                <div key={item.id} className="p-3 border-b last:border-0 flex justify-between text-sm">
                  <span className="font-medium">{item.name}</span>
                  <span className="text-gray-500">{item.id}</span>
                </div>
              ))}
              {assetTypes.data?.length === 0 && <div className="text-gray-500 py-4">Пусто</div>}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="liability-types">
          <Card>
            <CardHeader><CardTitle>Типы обязательств</CardTitle></CardHeader>
            <CardContent>
              {liabilityTypes.isLoading && <div className="space-y-2">{[1,2,3].map(i=><Skeleton key={i} className="h-10 w-full"/>)}</div>}
              {liabilityTypes.isError && <div className="text-red-500">Ошибка загрузки</div>}
              {liabilityTypes.data?.map((item) => (
                <div key={item.id} className="p-3 border-b last:border-0 flex justify-between text-sm">
                  <span className="font-medium">{item.name}</span>
                  <span className="text-gray-500">{item.id}</span>
                </div>
              ))}
              {liabilityTypes.data?.length === 0 && <div className="text-gray-500 py-4">Пусто</div>}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="categories">
          <Card>
            <CardHeader><CardTitle>Категории</CardTitle></CardHeader>
            <CardContent>
              {categories.isLoading && <div className="space-y-2">{[1,2,3].map(i=><Skeleton key={i} className="h-10 w-full"/>)}</div>}
              {categories.isError && <div className="text-red-500">Ошибка загрузки</div>}
              {categories.data?.map((item) => (
                <div key={item.id} className="p-3 border-b last:border-0 flex justify-between text-sm">
                  <span className="font-medium">{item.name}</span>
                  <span className="text-gray-500">{item.id}</span>
                </div>
              ))}
              {categories.data?.length === 0 && <div className="text-gray-500 py-4">Пусто</div>}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
